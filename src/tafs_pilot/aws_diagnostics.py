"""AWS environment diagnostics for Taf's Pilot.

Performs safe, read-only inspection of the standard AWS credential provider chain,
STS identity, Amazon Bedrock foundation models, Amazon Polly, and Amazon Titan Image Generator.
Never prints or logs secret access keys, tokens, or credentials.
"""

from typing import Any, Dict, List, Optional
import boto3
from botocore.exceptions import ClientError, EndpointConnectionError, NoCredentialsError, PartialCredentialsError

from tafs_pilot.config import (
    check_aws_credentials,
    get_configured_aws_region,
    get_configured_bedrock_model_id,
)


def run_aws_diagnostics(region: Optional[str] = None) -> Dict[str, Any]:
    """Inspects the current AWS environment and returns a structured diagnostic report."""
    target_region = region or get_configured_aws_region()
    configured_model = get_configured_bedrock_model_id()
    has_creds, cred_status = check_aws_credentials()

    report: Dict[str, Any] = {
        "region": target_region,
        "credentials_available": has_creds,
        "credential_source": cred_status,
        "account_id": None,
        "caller_arn": None,
        "bedrock_accessible": False,
        "bedrock_models": [],
        "target_model_invokable": False,
        "polly_accessible": False,
        "polly_voices_sample": [],
        "titan_image_accessible": False,
        "blockers": [],
    }

    if not has_creds:
        report["blockers"].append("No AWS credentials located in environment, CLI profile, or IAM role.")
        return report

    session = boto3.Session(region_name=target_region)

    # 1. Inspect STS caller identity
    try:
        sts = session.client("sts", region_name=target_region)
        caller = sts.get_caller_identity()
        report["account_id"] = caller.get("Account")
        report["caller_arn"] = caller.get("Arn")
    except Exception as e:
        report["blockers"].append(f"STS get_caller_identity failed: {type(e).__name__} ({str(e)[:120]})")

    # 2. Inspect Amazon Polly access
    try:
        polly = session.client("polly", region_name=target_region)
        voices_resp = polly.describe_voices(LanguageCode="en-US")
        voices = [v.get("Id") for v in voices_resp.get("Voices", [])[:5]]
        report["polly_accessible"] = True
        report["polly_voices_sample"] = voices
    except Exception as e:
        report["blockers"].append(f"Amazon Polly describe_voices failed: {type(e).__name__} ({str(e)[:120]})")

    # 3. Inspect Amazon Bedrock access
    try:
        bedrock = session.client("bedrock", region_name=target_region)
        models_resp = bedrock.list_foundation_models(
            byOutputModality="TEXT",
            byInferenceType="ON_DEMAND",
        )
        model_ids = [
            m.get("modelId")
            for m in models_resp.get("modelSummaries", [])
            if m.get("modelLifecycle", {}).get("status", "").upper() == "ACTIVE"
        ]

        # Also inspect active Bedrock inference profiles
        inference_profiles: List[str] = []
        try:
            prof_resp = bedrock.list_inference_profiles(typeEquals="SYSTEM_DEFINED")
            inference_profiles = [
                p.get("inferenceProfileId")
                for p in prof_resp.get("inferenceProfileSummaries", [])
                if p.get("status", "").upper() == "ACTIVE" and "inferenceProfileId" in p
            ]
        except Exception:
            pass

        all_active_models = model_ids + inference_profiles
        report["bedrock_accessible"] = True
        report["bedrock_models"] = model_ids
        report["bedrock_inference_profiles"] = inference_profiles

        # Check if configured model is in active foundation models or inference profiles
        if configured_model and (configured_model in all_active_models):
            report["target_model_invokable"] = True
    except Exception as e:
        report["blockers"].append(f"Amazon Bedrock list_foundation_models failed: {type(e).__name__} ({str(e)[:120]})")

    # 4. Inspect Amazon Titan Image Generator access
    try:
        bedrock = session.client("bedrock", region_name=target_region)
        image_resp = bedrock.list_foundation_models(
            byOutputModality="IMAGE",
            byInferenceType="ON_DEMAND",
        )
        titan_models = [
            m.get("modelId")
            for m in image_resp.get("modelSummaries", [])
            if "titan-image" in m.get("modelId", "")
        ]
        if titan_models:
            report["titan_image_accessible"] = True
    except Exception as e:
        report["blockers"].append(f"Amazon Titan image query failed: {type(e).__name__} ({str(e)[:120]})")

    return report
