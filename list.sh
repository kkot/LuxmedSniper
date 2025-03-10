#!/bin/bash
set -e

# List only active CloudFormation stacks (not deleted ones)
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE UPDATE_ROLLBACK_COMPLETE \
  --query "StackSummaries[*].[StackName,StackStatus,to_string(CreationTime),to_string(LastUpdatedTime)]" \
  --output table | 
  # Remove milliseconds and timezone information
  sed -E 's/([0-9]{4}-[0-9]{2}-[0-9]{2})T([0-9]{2}:[0-9]{2}:[0-9]{2})\.[0-9]+\+[0-9]{2}:[0-9]{2}/\1 \2/g' 