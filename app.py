#!/usr/bin/env python3
import os

from aws_cdk import core as cdk

from aws_cdk import core

from cdk_stripe_chartmogul_sync.cdk_stripe_chartmogul_sync_stack import (
    CdkStripeChartmogulSyncStack,
)


app = core.App()
CdkStripeChartmogulSyncStack(
    app,
    "CdkStripeChartmogulSyncStack",
)

app.synth()
