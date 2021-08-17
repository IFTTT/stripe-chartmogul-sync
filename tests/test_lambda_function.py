import pytest

from functions.stripe_chartmogul_sync import index as lambda_function

# Disable XRay during unit testing
from aws_xray_sdk.sdk_config import SDKConfig

SDKConfig.set_sdk_enabled(False)


class TestServiceHandler:
    @pytest.fixture
    def event(self):
        return "Test"

    def test_lambda_handler(self):
        result = lambda_function.handler(self.event, None)
        assert result == {"statusCode": 200}
