import boto3
import json

print("Testing Amazon Nova model (no Anthropic restrictions)...")
print("=" * 60)

bedrock_runtime = boto3.client("bedrock-runtime", region_name="us-east-1")

# Try Amazon Nova Pro (Amazon's own model - no provider restrictions)
model_id = "us.amazon.nova-pro-v1:0"

print(f"\nTesting: {model_id}")
print("-" * 60)

try:
    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        body=json.dumps({
            "messages": [{"role": "user", "content": [{"text": "Write a SQL query: SELECT 1"}]}],
            "inferenceConfig": {"max_new_tokens": 100}
        })
    )
    
    print("✅ SUCCESS! Nova model works!")
    result = json.loads(response['body'].read())
    print(f"Response: {str(result)[:200]}...")
    
    # Save working model
    with open("working_model.txt", "w") as f:
        f.write(model_id)
    print(f"\n🎉 WORKING MODEL: {model_id}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTrying Amazon Nova Lite instead...")
    
    try:
        model_id = "us.amazon.nova-lite-v1:0"
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps({
                "messages": [{"role": "user", "content": [{"text": "Write a SQL query: SELECT 1"}]}],
                "inferenceConfig": {"max_new_tokens": 100}
            })
        )
        print("✅ SUCCESS! Nova Lite works!")
        with open("working_model.txt", "w") as f:
            f.write(model_id)
        print(f"🎉 WORKING MODEL: {model_id}")
    except Exception as e2:
        print(f"❌ Also failed: {e2}")
        print("\nAll models tested failed. Account may need admin activation.")
