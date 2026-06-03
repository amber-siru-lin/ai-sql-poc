import sys
from pathlib import Path

import boto3

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from config.settings import aws_region, bedrock_model_id
WORKING_MODEL_PATH = REPO_ROOT / "config" / "working_model.txt"

region = aws_region()
model_id = bedrock_model_id()

print("AWS Bedrock Diagnostic Tool")
print("=" * 60)
print(f"Region: {region}")
print(f"Model:  {model_id}")

bedrock = boto3.client("bedrock", region_name=region)
bedrock_runtime = boto3.client("bedrock-runtime", region_name=region)

print("\n1. Checking for INFERENCE PROFILES in your account...")
print("-" * 60)
try:
    profiles = bedrock.list_inference_profiles()
    if profiles.get("inferenceProfileSummaries"):
        for profile in profiles["inferenceProfileSummaries"]:
            print(f"✅ Profile: {profile['inferenceProfileName']}")
            print(f"   ID: {profile.get('inferenceProfileId', 'N/A')}")
            print(f"   ARN: {profile['inferenceProfileArn']}")
    else:
        print("❌ No inference profiles found")
except Exception as exc:
    print(f"❌ Error listing profiles: {exc}")

print("\n2. Testing configured Bedrock model...")
print("-" * 60)
print(f"Model ID: {model_id}")
try:
    response = bedrock_runtime.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": "Say hello in one word."}]}],
        inferenceConfig={"maxTokens": 10},
    )
    text = response["output"]["message"]["content"][0]["text"]
    print(f"✅ SUCCESS! Response: {text}")
    WORKING_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    WORKING_MODEL_PATH.write_text(model_id, encoding="utf-8")
    print(f"Saved working model to {WORKING_MODEL_PATH}")
except Exception as exc:
    error = str(exc)
    if "ExpiredToken" in error:
        print("❌ AWS credentials expired — run: aws sso login --profile $AWS_PROFILE")
    else:
        print(f"❌ Error: {error[:200]}")

print("\n" + "=" * 60)
print("Diagnostic complete!")
