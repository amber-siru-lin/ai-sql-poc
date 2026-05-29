import boto3
import json

print("AWS Bedrock Diagnostic Tool")
print("=" * 60)

# Create clients
bedrock = boto3.client("bedrock", region_name="us-east-1")
bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-east-1")

# Check 1: List inference profiles (not foundation models)
print("\n1. Checking for INFERENCE PROFILES in your account...")
print("-" * 60)
try:
    profiles = bedrock.list_inference_profiles()
    if profiles.get('inferenceProfileSummaries'):
        for profile in profiles['inferenceProfileSummaries']:
            print(f"✅ Profile: {profile['inferenceProfileName']}")
            print(f"   ID: {profile.get('inferenceProfileId', 'N/A')}")
            print(f"   ARN: {profile['inferenceProfileArn']}")
            print(f"   Status: {profile.get('status', 'N/A')}")
            print(f"   Type: {profile.get('type', 'N/A')}")
    else:
        print("❌ No inference profiles found")
        print("   You need to create one or your account needs model access approval")
except Exception as e:
    print(f"❌ Error listing profiles: {e}")

# Check 2: Try invoking with different formats
print("\n2. Testing different invocation methods...")
print("-" * 60)

models_to_try = [
    # Format 1: Direct model ID (legacy)
    ("Direct model ID", "anthropic.claude-3-5-haiku-20241022-v1:0"),
    # Format 2: US inference profile
    ("US inference profile", "us.anthropic.claude-3-5-haiku-20241022-v1:0"),
    # Format 3: Global inference profile  
    ("Global inference profile", "global.anthropic.claude-3-5-haiku-20241022-v1:0"),
    # Format 4: Try Sonnet 4 with us prefix
    ("US Sonnet 4", "us.anthropic.claude-sonnet-4-20250514-v1:0"),
    # Format 5: Try global Sonnet 4
    ("Global Sonnet 4", "global.anthropic.claude-sonnet-4-20250514-v1:0"),
]

for desc, model_id in models_to_try:
    print(f"\nTesting: {desc}")
    print(f"Model ID: {model_id}")
    try:
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Say hello"}]
            })
        )
        print("✅ SUCCESS! This model works")
        print(f"Response: {str(response)[:100]}...")
        
        # If this works, save it!
        with open("working_model.txt", "w") as f:
            f.write(model_id)
        print(f"\n🎉 FOUND WORKING MODEL: {model_id}")
        print("Saved to working_model.txt")
        break
        
    except Exception as e:
        error = str(e)
        if "Legacy" in error:
            print("❌ Model marked as Legacy (need use case details?)")
        elif "on-demand throughput" in error:
            print("❌ Requires inference profile (not direct model)")
        elif "Access denied" in error:
            print("❌ Access denied (need permissions)")
        elif "ResourceNotFound" in error:
            print("❌ Model not found (wrong ID)")
        else:
            print(f"❌ Error: {error[:100]}")

# Check 3: Check account-level requirements
print("\n3. Checking account requirements...")
print("-" * 60)
print("If you see 'Legacy' errors for ALL models, you may need to:")
print("  - Submit use case details for Anthropic models")
print("  - Or your account admin needs to activate Bedrock")
print("\nIf you see 'on-demand throughput' errors, the model needs inference profiles")
print("  - Try the IDs from section 1 above")
print("  - Or create an application inference profile")

print("\n" + "=" * 60)
print("Diagnostic complete!")
