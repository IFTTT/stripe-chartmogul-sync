import os
import json
import datetime

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

        return {"statusCode": 500}

    return {"statusCode": 200}
