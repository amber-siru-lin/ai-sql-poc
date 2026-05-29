#!/bin/bash
# AWS Setup Helper Script
# Run this to configure AWS credentials for Bedrock access

echo "============================================"
echo "AWS CREDENTIALS SETUP HELPER"
echo "============================================"
echo ""
echo "To use AWS Bedrock, you need:"
echo "1. AWS Access Key ID"
echo "2. AWS Secret Access Key"
echo "3. AWS Region (e.g., us-east-1)"
echo ""
echo "Do you have these credentials?"
echo "  - If YES: Continue below"
echo "  - If NO: You need to create them first"
echo ""

# Check if user has credentials
read -p "Do you have AWS credentials? (yes/no): " has_creds

if [ "$has_creds" != "yes" ] && [ "$has_creds" != "YES" ]; then
    echo ""
    echo "⚠️  You need to create AWS credentials first:"
    echo ""
    echo "Option 1: Use your company's AWS account"
    echo "  - Ask your IT team for AWS access"
    echo "  - They will give you Access Key + Secret Key"
    echo ""
    echo "Option 2: Create your own AWS account (free)"
    echo "  1. Go to: https://aws.amazon.com/free/"
    echo "  2. Sign up with your email"
    echo "  3. Go to: IAM Console → Users → Create User"
    echo "  4. Attach policy: 'AmazonBedrockFullAccess'"
    echo "  5. Create Access Key (save the CSV!)"
    echo ""
    echo "Option 3: Use AWS SSO (if your company has it)"
    echo "  - Run: aws sso login"
    echo "  - Follow the browser prompts"
    echo ""
    echo "Once you have credentials, run this script again."
    echo ""
    exit 1
fi

echo ""
echo "Enter your AWS credentials:"
echo "(These will be saved to ~/.aws/credentials)"
echo ""

read -p "AWS Access Key ID: " access_key
read -p "AWS Secret Access Key: " secret_key
read -p "AWS Region [us-east-1]: " region

# Default to us-east-1 if not provided
region=${region:-us-east-1}

# Create AWS config directory
mkdir -p ~/.aws

# Write credentials file
cat > ~/.aws/credentials << EOF
[default]
aws_access_key_id = $access_key
aws_secret_access_key = $secret_key
EOF

# Write config file
cat > ~/.aws/config << EOF
[default]
region = $region
output = json
EOF

# Set secure permissions
chmod 600 ~/.aws/credentials
chmod 600 ~/.aws/config

echo ""
echo "✅ AWS credentials configured!"
echo ""
echo "Testing connection..."
aws sts get-caller-identity 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ AWS connection successful!"
    echo ""
    echo "Next step: Test Bedrock access"
    echo "Run: aws bedrock list-foundation-models --region $region"
else
    echo ""
    echo "❌ AWS connection failed. Check your credentials."
    echo "Common issues:"
    echo "  - Wrong Access Key ID (should start with 'AKIA...')"
    echo "  - Wrong Secret Key (long string with +, /, =)"
    echo "  - Account doesn't have Bedrock permissions"
fi
