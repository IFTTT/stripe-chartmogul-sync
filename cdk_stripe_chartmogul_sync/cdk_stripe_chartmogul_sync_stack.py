import os
import logging

from aws_cdk import core as cdk

from aws_cdk import aws_iam
from aws_cdk import aws_logs
from aws_cdk import aws_lambda
from aws_cdk import aws_lambda_python
from aws_cdk import aws_events
from aws_cdk import aws_events_targets

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class CdkStripeChartmogulSyncStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Required environment variable
        stripe_api_key_arn = os.getenv("STRIPE_API_KEY_ARN")
        if not stripe_api_key_arn:
            raise Exception(
                "Unable to get Stripe API key ARN from environment: STRIPE_API_KEY_ARN"
            )

        # Required environment variable
        chartmogul_api_key_arn = os.getenv("CHARTMOGUL_API_KEY_ARN")
        if not chartmogul_api_key_arn:
            raise Exception(
                "Unable to get Stripe API key ARN from environment: STRIPE_API_KEY_ARN"
            )

        # Lambda function to check signature and push to SQS
        stripe_chartmogul_sync_function = aws_lambda_python.PythonFunction(
            self,
            "StripeChartMogulSync",
            description="Syncs customer information between Stripe and ChartMogul",
            entry="functions/stripe_chartmogul_sync",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
            tracing=aws_lambda.Tracing.ACTIVE,
            environment={
                "STRIPE_API_KEY_ARN": stripe_api_key_arn,
                "CHARTMOGUL_API_KEY_ARN": chartmogul_api_key_arn,
            },
        )

        # Give the function permissions
        stripe_chartmogul_sync_function.add_to_role_policy(
            aws_iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                effect=aws_iam.Effect.ALLOW,
                resources=[stripe_api_key_arn, chartmogul_api_key_arn],
            )
        )

        # The rule that sends Stripe events to the Lambda function
        aws_events.Rule(
            self,
            "StripeChartMogulSyncRule",
            description="Rule for sending events to the Stripe ChartMogul sync function",
            enabled=True,
            event_pattern={"source": ["stripe"]},
            targets=[
                aws_events_targets.LambdaFunction(stripe_chartmogul_sync_function)
            ],
        )
