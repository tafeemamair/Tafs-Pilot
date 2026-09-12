"""Configuration and AWS credential resolution utilities for Taf's Pilot."""

import os
from typing import Optional, Tuple
import boto3
from dotenv import load_dotenv

# Load local environment variables if a .env file exists
load_dotenv()


def get_configured_aws_region() -> str:
    """Returns the configured AWS region, checking env vars and standard AWS defaults."""
    return os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"


def get_configured_bedrock_model_id() -> str:
    """Returns the configured Bedrock Model ID, defaulting to verified profile us.openai.gpt-6-astra."""
    return os.getenv("BEDROCK_MODEL_ID") or "us.openai.gpt-6-astra"


def check_aws_credentials() -> Tuple[bool, str]:
    """Checks whether valid AWS credentials can be resolved via the standard provider chain."""
    try:
        session = boto3.Session()
        creds = session.get_credentials()
        if creds is None:
            return False, "No AWS credentials found via environment, AWS CLI profile, or IAM role."
        return True, f"AWS credentials found (Access Key: {creds.access_key[:4]}***)"
    except Exception as e:
        return False, f"Error resolving AWS credentials: {str(e)}"
