import boto3
import json

print("Creating Application Inference Profile...")
print("=" * 60)

# Create Bedrock client
bedrock = boto3.client("bedrock", region_name="us-east-1")

# Try to create an inference profile for Claude 3.5 Sonnet
# This should "activate" the model for your account
profile_name = "sql-poc-profile"

# Use a newer model that should be active
try:
    response = bedrock.create_inference_profile(
        inferenceProfileName=profile_name,
        description="POC for NL to SQL generation",
        modelSource={
            "copyFrom": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
        }
    )
    
    print("✅ Inference profile created successfully!")
    print(f"ARN: {response['inferenceProfileArn']}")
    print(f"Status: {response['status']}")
    
    # Save the ARN for use in the main script
    with open("inference_profile_arn.txt", "w") as f:
        f.write(response['inferenceProfileArn'])
    
    print("\n📝 ARN saved to inference_profile_arn.txt")
    print("\nNext step: Update test_ai_sql.py with this ARN:")
    print(f'model_id="{response["inferenceProfileArn"]}"')
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nPossible reasons:")
    print("1. You don't have permission to create inference profiles")
    print("2. The model requires admin approval first")
    print("3. Your account needs to submit use case details")
    print("\nTry Option B or C instead.")
