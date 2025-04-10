#!/bin/bash
set -e

# Configuration - change these values as needed
FUNCTION_NAME="LuxMedSniper"
REGION="eu-west-1"
HOURS=1

# Calculate start time (last X hours)
START_TIME=$(date -u -v-${HOURS}H +%s000 2>/dev/null || date -u -d "-${HOURS} hours" +%s000)
LOG_GROUP_NAME="/aws/lambda/$FUNCTION_NAME"

echo "Reading logs for Lambda function: $FUNCTION_NAME"
echo "Region: $REGION"
echo "Time range: Last $HOURS hour(s)"
echo "-------------------------------------------"

# Get logs across all streams within the timeframe
aws logs filter-log-events \
  --log-group-name "$LOG_GROUP_NAME" \
  --start-time "$START_TIME" \
  --region "$REGION" \
  --query "events[*].message" \
  --output text \
  --no-cli-pager

echo "-------------------------------------------" 