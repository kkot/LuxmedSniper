#!/bin/bash
set -e

# Configuration - change these values as needed
FUNCTION_NAME="LuxMedSniper"
REGION="eu-west-1"
HOURS=24

# Calculate start time (last 24 hours by default)
START_TIME=$(date -u -v-${HOURS}H +%s000 2>/dev/null || date -u -d "-${HOURS} hours" +%s000)
LOG_GROUP_NAME="/aws/lambda/$FUNCTION_NAME"

echo "Reading logs for Lambda function: $FUNCTION_NAME"
echo "Region: $REGION"
echo "Time range: Last $HOURS hour(s)"
echo "-------------------------------------------"

# Get log streams sorted by last event time
STREAMS=$(aws logs describe-log-streams \
  --log-group-name "$LOG_GROUP_NAME" \
  --order-by LastEventTime \
  --descending \
  --region "$REGION" \
  --query "logStreams[*].logStreamName" \
  --output text)

if [ -z "$STREAMS" ]; then
  echo "No log streams found. The function might not have been executed yet."
  exit 1
fi

# For each stream, get the logs
for STREAM in $STREAMS; do
  echo "Log stream: $STREAM"
  echo "-------------------------------------------"
  
  # Get logs from the stream
  aws logs get-log-events \
    --log-group-name "$LOG_GROUP_NAME" \
    --log-stream-name "$STREAM" \
    --start-time "$START_TIME" \
    --region "$REGION" \
    --query "events[*].[timestamp,message]" \
    --output text | while read -r TIMESTAMP MESSAGE; do
      # Convert timestamp to human-readable format - handle empty timestamps
      if [[ -n "$TIMESTAMP" && "$TIMESTAMP" =~ ^[0-9]+$ ]]; then
        # Divide by 1000 to convert milliseconds to seconds
        SECONDS=$((TIMESTAMP / 1000))
        DATE=$(date -r "$SECONDS" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || date -d "@$SECONDS" "+%Y-%m-%d %H:%M:%S")
        echo "[$DATE] $MESSAGE"
      else
        # If timestamp is not a number, just print the message
        echo "$MESSAGE"
      fi
    done
  
  echo "-------------------------------------------"
done 