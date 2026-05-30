# Quick test to check which models work with your AWS account
# Run this to test connectivity without LangChain complexity

import boto3
import json

# List of models to test (common ones that might work)
models_to_test = [
    "anthropic.claude-3-5-haiku-20241022-v1:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
    "amazon.titan-text-express-v1",
    "amazon.titan-text-lite-v1",
    "meta.llama3-8b-instruct-v1:0",
]

print("Testing AWS Bedrock model access...")
print("=" * 60)

bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

for model_id in models_to_test:
    print(f"\nTesting: {model_id}")
    print("-" * 40)
    
    try:
        # Try a simple invoke
        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps({
                "prompt": "Say hello",
                "max_tokens": 10
            })
        )
        
        print("✅ WORKS! Model is accessible")
        
        # Parse response
        response_body = json.loads(response['body'].read())
        print(f"Response: {str(response_body)[:100]}...")
        
    except Exception as e:
        error_msg = str(e)
        
        if "ResourceNotFoundException" in error_msg:
            print("❌ Model not found or requires inference profile")
        elif "ValidationException" in error_msg:
            print("❌ Validation error (might need inference profile)")
        elif "AccessDenied" in error_msg:
            print("❌ Access denied (need permissions)")
        elif "use case" in error_msg.lower() or "details" in error_msg.lower():
            print("❌ Need to submit use case details for this model")
        else:
            print(f"❌ Error: {error_msg[:100]}")

print("\n" + "=" * 60)
print("Testing complete!")
print("\nIf you see 'Need to submit use case details':")
print("1. Go to: https://console.aws.amazon.com/bedrock")
print("2. Click 'Model access' or look for Anthropic model request")
print("3. Submit use case form (takes 1-2 business days to approve)")
print("\nIf you see 'Works!': Use that model ID in test_ai_sql.py")
