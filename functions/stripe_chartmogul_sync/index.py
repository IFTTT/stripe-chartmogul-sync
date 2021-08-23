import os
import json
import datetime
import chartmogul
import pandas as pd
import re
from requests.api import get
import stripe
import promise
import requests as rq

import stripe
import boto3
import botocore
import logging

from aws_xray_sdk.core import patch_all
from aws_xray_sdk.core import xray_recorder

logger = logging.getLogger()
logger.setLevel(logging.INFO)

secrets_client = boto3.client("secretsmanager")
eventbridge_client = boto3.client("events")

# Instrument libraries for AWS XRay
patch_all()

def handler(event, context):
    logger.info("test")
    logger.info(f"Lambda event: {json.dumps(event)}")

    # Required environment variable
    stripe_api_key_arn = os.getenv("STRIPE_API_KEY_ARN")
    if not stripe_api_key_arn:
        logger.error(
            f"Unable to get Stripe API key ARN from environment: STRIPE_API_KEY_ARN"
        )

        return {"statusCode": 500}

    # Required environment variable
    chartmogul_api_key_arn = os.getenv("CHARTMOGUL_API_KEY_ARN")
    if not chartmogul_api_key_arn:
        logger.error(
            f"Unable to get ChartMogul API Key ARN from environment: CHARTMOGUL_API_KEY_ARN"
        )

    chartmogul_api_token_arn = os.getenv("CHARTMOGUL_API_TOKEN_ARN")
    if not chartmogul_api_token_arn:
        logger.error(
            f"Unable to get ChartMogul API Key ARN from environment: CHARTMOGUL_API_TOKEN_ARN"
        )

    try:
        # Required secret
        stripe_api_key = secrets_client.get_secret_value(SecretId=stripe_api_key_arn)[
            "SecretString"
        ]
    except botocore.exceptions.ClientError as e:
        logger.error(
            f"Unable to get Stripe API key from Secrets Manager: {stripe_api_key_arn}"
        )

        return {"statusCode": 500}

    try:
        # Required secret
        chartmogul_api_key = secrets_client.get_secret_value(
            SecretId=chartmogul_api_key_arn
        )["SecretString"]
    except botocore.exceptions.ClientError as e:
        logger.error(
            f"Unable to get ChartMogul API key from Secrets Manager: {chartmogul_api_key_arn}"
        )

    try:
        # Required secret
        chartmogul_api_token = secrets_client.get_secret_value(
            SecretId=chartmogul_api_token_arn
        )["SecretString"]
    except botocore.exceptions.ClientError as e:
        logger.error(
            f"Unable to get ChartMogul API token from Secrets Manager: {chartmogul_api_token_arn}"
        )

        return {"statusCode": 500}

    config = chartmogul.Config(chartmogul_api_token, chartmogul_api_key)

    return {"statusCode": 200}

# MATCHING APPROACH
# read customers from stripe - from events - grab customer_id, and read event type for relevancy
# read customer info in cm - check if they are there
    # if not there, we create customer, then read invoices and re-sync stripe invoices
    # if they are in cm, we read invoices from stripe and re-sync them
# cannot update invoices, must delete and recreate - will create probs on ther end
# must match the current invoices in cm to stripe, if they match move on, if not then delete and recreate

# Get source id - before you check each customer
def source_id():
    payload={"name":"Stripe Custom"}
    req = rq.get(
        "https://api.chartmogul.com/v1/data_sources",
        params = payload,
        auth=(CM_TOKEN, CM_SECRET)
    ).json()
    source_id = req['data_sources'][0]['uuid']

    return(source_id)
    
# create chartmogul plan
def upload_plan(invoice, source_id, platform):
    # constants
    if platform == "stripe":
        plan_id = invoice['data'][0]['lines']['data'][0]['plan']['id']
        interval_count = invoice['data'][0]['lines']['data'][0]['plan']['interval_count']
        interval_unit = invoice['data'][0]['lines']['data'][0]['plan']['interval']

    # upload
    res = chartmogul.Plan.create(
      config,
      data={
        "data_source_uuid": source_id,
        "interval_count": interval_count,
        "interval_unit": interval_unit,
        "external_id": plan_id
      })
    
    res = str(res)
    cm_plan_uuid = re.sub("^.*, uuid='", "", res)
    cm_plan_uuid = re.sub("', .*$", "", cm_plan_uuid)
    
    return(cm_plan_uuid)

def get_plan_id(ext_plan_id):
    req = rq.get(
        "https://api.chartmogul.com/v1/plans?external_id="+ext_plan_id
    ).json()
    return(req['uuid'])

# chartmogul upload customer - check if person exists, if not create them
def upload_customer(customer, source_id, platform):
    # create objects
    if platform == "stripe":
        customer_id = customer['id']
        customer_name = customer['name']
        customer_email = customer['email']
        plan_start = customer['subscriptions']['data'][0]['items']['data'][0]['plan']['created']
        plan_start = datetime.datetime.fromtimestamp(int(plan_start)).strftime('%Y-%m-%d %H:%M:%S')
        trial_start = customer['subscriptions']['data'][0]['trial_start']

    if trial_start != None:
        trial_start = datetime.datetime.fromtimestamp(int(trial_start)).strftime('%Y-%m-%d %H:%M:%S')
        # upload with trial date if available
        res = chartmogul.Customer.create(
        config,
        data={
            "data_source_uuid": source_id,
            "external_id": customer_id,
            "name": customer_name,
            "email": customer_email,
            "lead_created_at": plan_start,
            "free_trial_started_at": trial_start
        })
    else:
        res = chartmogul.Customer.create(
        config,
        data={
            "data_source_uuid": source_id,
            "external_id": customer_id,
            "name": customer_name,
            "email": customer_email,
            "lead_created_at": plan_start
        })

    cm_cus_uuid = res.entries[0].uuid
        
    return(cm_cus_uuid)

# upload invoices to chartmogul
def upload_invoice(invoice, cm_customer_id, cm_plan_id, cm_source_id, platform):
    # constants
    if platform == "stripe":
        inv_items = {"invoices": []}

        for invoice in stripe_invoices["data"]:
            invoice_date = invoice['date']
            due_date = invoice['due_date']
            period_start = invoice['lines']['data'][0]['period']['start']
            period_end = invoice['lines']['data'][0]['period']['end']
            trans_date = invoice['status_transitions']['paid_at']
            if invoice['status'] == 'paid': trans_type = 'payment'
            else: trans_type = 'refund'
            if invoice['status'] == 'paid': trans_result = 'successful'
            else: trans_result = 'failed'

            xx= {
                "external_id": invoice['id'],
                "date": datetime.datetime.fromtimestamp(int(invoice_date)).strftime('%Y-%m-%d %H:%M:%S'),
                "currency": invoice['currency'].upper(),
                "due_date": datetime.datetime.fromtimestamp(int(due_date)).strftime('%Y-%m-%d %H:%M:%S'),
                "customer_external_id": invoice['customer'],
                "data_source_uuid": cm_source_id,
                "line_items": [
                    {
                        "type": "subscription",
                        "subscription_external_id": invoice['subscription'],
                        "plan_uuid": cm_plan_id,
                        "service_period_start": datetime.datetime.fromtimestamp(int(period_start)).strftime('%Y-%m-%d %H:%M:%S'),
                        "service_period_end": datetime.datetime.fromtimestamp(int(period_end)).strftime('%Y-%m-%d %H:%M:%S'),
                        "amount_in_cents": int(invoice['lines']['data'][0]['plan']['amount_decimal']),
                        "quantity": invoice['lines']['data'][0]['quantity']
                    }
                ],
                "transactions": [
                    {
                        "date": trans_date,
                        "type": trans_type,
                        "result": trans_result
                    }
                ]
            }
            inv_items['invoices'].append(xx)


    # upload
    res = chartmogul.Invoice.create(
    config,
    uuid= cm_customer_id,
    data={
        "invoices": [xx]
    })
    
    res = str(res)
    cm_inv_uuid = re.sub("^.*, uuid='", "", res)
    cm_inv_uuid = re.sub("', .*$", "", cm_inv_uuid)
    
    return(res)

# check events for relevants
def update_invoices(event, source_id):
    if event['detail-type'] in (
        "invoice.payment_succeeded",
        "customer.subscription.updated",
        "customer.subscription.deleted",
        "customer.subscription.created"
    ):
        # get constants
        str_customer_id = event['detail']['data']['object']['customer']

        # check 
        cm_customer = chartmogul.Customer.all(config, external_id = str_customer_id).get()
        cm_customer.entries[0].uuid != None
        cm_bitsy_uuid = "cus_aee9d49e-fa39-11eb-9806-93fd124dec52"

        # if customer exists check invoices
        if cm_customer.entries[0].uuid != None:
            cm_cus_uuid = cm_customer.entries[0].uuid
            data_source_uuid = cm_customer.entries[0].data_source_uuid

            # get invoice ids for stripe and chartmogul
            inv_url = "https://api.chartmogul.com/v1/import/customers/"+cm_cus_uuid+"/invoices"
            cm_inv =rq.get(
                inv_url,
                auth=(CM_TOKEN, CM_SECRET)
            ).json()

            cm_invoice_ids = []
            for invoice in cm_inv['invoices']:
                cm_invoice_ids.append(invoice['external_id'])

            stripe_invoices= stripe.Invoice.list(customer = str_customer_id)

            str_invoice_ids = []
            for invoice in stripe_invoices["data"]:
                str_invoice_ids.append(invoice['id'])

            str_plan_ids = []
            for invoice in stripe_invoices["data"]:
                str_plan_ids.append(invoice['lines']['data'][0]['plan']['id'])
            
            # check to see if invoice ids in stripe match what is in chartmogul
            if str_invoice_ids in cm_invoice_ids:
                return{"status code": 200}
            else:
                for uuid in cm_invoice_ids:
                    chartmogul.Invoice.destroy(config, uuid = uuid)

            # upload invoices to chartmogul if they do not match
            for invoice in stripe_invoices:
                for plan_id in str_plan_ids:
                    cm_plan_id = get_plan_id(plan_id)
                    upload_invoice(invoice, cm_cus_uuid, cm_plan_id, source_id, platform = "stripe")

        # create new customer and upload all invoices if they do not already exist
        else:
            customer = upload_customer(event, "ds_c52fc4d6-f627-11eb-9764-33db032012f1", platform = "stripe")
            for invoice in stripe_invoices:
                for plan_id in str_plan_ids:
                    cm_plan_id = get_plan_id(plan_id)
                    upload_invoice(invoice, customer, cm_plan_id, source_id, platform = "stripe")
