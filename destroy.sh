#!/bin/bash
set -e

# Configuration - change these values as needed
STACK_NAME="LuxMedSniperStack"
REGION="eu-west-1"

echo "Starting deletion of LuxMed Sniper Lambda stack..."
echo "Stack name: $STACK_NAME"
echo "Region: $REGION"
echo "-------------------------------------------"

# Confirm deletion
read -p "Are you sure you want to delete this stack? (y/n): " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
  echo "Deletion cancelled."
  exit 0
fi

# Delete the CloudFormation stack
echo "Deleting CloudFormation stack: $STACK_NAME"
aws cloudformation delete-stack \
  --stack-name "$STACK_NAME" \
  --region "$REGION"

echo "Stack deletion initiated. Waiting for completion..."

# Wait for the stack to be deleted
aws cloudformation wait stack-delete-complete \
  --stack-name "$STACK_NAME" \
  --region "$REGION"

echo "Stack deletion completed successfully!"
echo "-------------------------------------------"

# Optional: List S3 buckets that might need manual cleanup
echo "Note: S3 buckets created by the deployment script might still exist."
echo "You may want to check and delete them manually if needed:"
aws s3 ls | grep "luxmed-sniper-lambda" 