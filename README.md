
# Stripe ChartMogul Sync

![Architecture](/assets/architecture.png)

A serverless CDK-based pipeline for syncing Stripe data with ChartMogul

This CDK registers a Lambda Function with EventBridge that processes Stripe events. The Lambda Function performs a one-way sync of the customer and related invoices from Stripe to ChartMogul.

![Sequence Diagram](/assets/sequence-diagram.png)

## Setup

- Create the virtual environment: `python3 -m venv .venv`
- Enable the virtual environment: `source .venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`
- Deploy the stack: `cdk deploy`

## Events
- This pipeline listens for Stripe events on the `$default` Event Bus with the following rule:
  - `source == stripe`

## Design Notes

- Events can arrive from Stripe [out of order](https://stripe.com/docs/webhooks/best-practices#event-ordering), which is why this process has a brute force design that ignores the event payload. Instead, the Lambda Function is simply triggered when a customer has changed in some way.
- Events can flow into this pipeline from anywhere. Typically the two sources are Stripe webhook events or a reconsiliation process that might be run to update customer records that might be out of sync.

## Testing Locally
[https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-cdk-getting-started.html](Install) the preview version of the SAM CLI.

```
$ sam-beta-cdk --version
SAM CLI, version 1.22.0.dev202107140310


```