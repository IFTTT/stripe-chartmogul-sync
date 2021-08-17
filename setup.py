import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="cdk_stripe_chartmogul_sync",
    version="1.0.0",
    description="A serverless CDK-based pipeline for syncing Stripe data with ChartMogul",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="IFTTT",
    install_requires=[
        "aws-cdk.core==1.117.0",
        "aws_cdk.aws_events==1.117.0",
        "aws_cdk.aws_events_targets==1.117.0",
        "aws_cdk.aws_secretsmanager==1.117.0",
        "aws_cdk.aws_lambda_python==1.117.0",
        "aws_xray_sdk == 2.8.0",
        "boto3==1.18.18",
        "boto3-stubs[essential,secretsmanager, events]",
        "stripe==2.60.0",
        "aws_xray_sdk == 2.8.0",
        "python-dotenv == 0.19.0",
        "pytest",
        "black",
    ],
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
)
