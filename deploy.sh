#!/bin/bash
set -e

# Configuration
STACK_NAME="LuxMedSniperStack"
S3_BUCKET_NAME="luxmed-sniper-lambda-$(date +%s)"
S3_KEY="luxmed-sniper-lambda.zip"
REGION="eu-west-1"  # Change to your preferred region

echo "Starting deployment of LuxMed Sniper Lambda..."

# Create a temporary directory for packaging
TEMP_DIR=$(mktemp -d)
echo "Created temporary directory: $TEMP_DIR"

# Copy necessary files to the temporary directory
cp luxmed_sniper.py lambda_handler.py luxmed_sniper.yaml account.yaml "$TEMP_DIR/"
echo "Copied files to temporary directory"

# Install dependencies to the temporary directory
pip install -r requirements.txt -t "$TEMP_DIR/"
echo "Installed dependencies"

# Create a zip file
cd "$TEMP_DIR"
zip -r "$S3_KEY" .
cd -
mv "$TEMP_DIR/$S3_KEY" .
echo "Created deployment package: $S3_KEY"

# Create S3 bucket if it doesn't exist
if ! aws s3api head-bucket --bucket "$S3_BUCKET_NAME" 2>/dev/null; then
    echo "Creating S3 bucket: $S3_BUCKET_NAME"
    aws s3 mb "s3://$S3_BUCKET_NAME" --region "$REGION"
else
    echo "S3 bucket already exists: $S3_BUCKET_NAME"
fi

# Upload the zip file to S3
echo "Uploading deployment package to S3..."
aws s3 cp "$S3_KEY" "s3://$S3_BUCKET_NAME/$S3_KEY"

# Deploy the CloudFormation stack
echo "Deploying CloudFormation stack: $STACK_NAME"
aws cloudformation deploy \
    --template-file template.yaml \
    --stack-name "$STACK_NAME" \
    --parameter-overrides \
        LambdaCodeBucket="$S3_BUCKET_NAME" \
        LambdaCodeKey="$S3_KEY" \
    --capabilities CAPABILITY_IAM \
    --region "$REGION"

# Clean up
rm -rf "$TEMP_DIR"
rm "$S3_KEY"

echo "Deployment completed successfully!"
echo "Stack name: $STACK_NAME"
echo "Lambda function: LuxMedSniper" 