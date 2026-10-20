# LuxMed Sniper - AWS Lambda Deployment

This guide explains how to deploy the LuxMed Sniper as an AWS Lambda function that runs every 60 seconds.

## Prerequisites

1. AWS CLI installed and configured with appropriate credentials
2. Python 3.11 or later
3. pip (Python package manager)
4. zip utility

## Deployment Steps

### 1. Prepare Configuration Files

Make sure your `luxmed_sniper.yaml` and `account.yaml` files are properly configured with your LuxMed credentials and notification preferences.

### 2. Deploy Using the Script

The easiest way to deploy is to use the provided deployment script:

```bash
./deploy.sh
```

This script will:
1. Create a temporary directory
2. Copy necessary files
3. Install dependencies
4. Create a deployment package (ZIP file)
5. Create an S3 bucket (if it doesn't exist)
6. Upload the deployment package to S3
7. Deploy the CloudFormation stack
8. Clean up temporary files

## Monitoring

You can monitor the Lambda function execution in the AWS Management Console:

1. Go to the Lambda service
2. Select the "LuxMedSniper" function
3. Check the "Monitor" tab to see execution metrics and logs

You can also view the logs in CloudWatch Logs:

1. Go to the CloudWatch service
2. Select "Log groups"
3. Find the "/aws/lambda/LuxMedSniper" log group
4. View the log streams to see the execution logs

### Log Monitoring Script

A simple script is provided to help you read logs from your Lambda function:

```bash
./simple_logs.sh
```

This script will:
- Read logs from the "LuxMedSniper" Lambda function
- Show logs from the last 24 hours
- Display timestamps in a human-readable format
- Show all log streams in descending order (newest first)

If you need to change any settings, you can edit these values at the top of the script:

```bash
# Configuration - change these values as needed
FUNCTION_NAME="LuxMedSniper"
REGION="eu-west-1"
HOURS=24
```

## Cleanup

When you no longer need the Lambda function, you can delete all AWS resources using the destroy script:

```bash
./destroy.sh
```

This script will:
1. Ask for confirmation before proceeding
2. Delete the CloudFormation stack
3. Wait for the deletion to complete
4. List any S3 buckets that might need manual cleanup

If you need to change any settings, you can edit these values at the top of the script:

```bash
# Configuration - change these values as needed
STACK_NAME="LuxMedSniperStack"
REGION="eu-west-1"
```

## Customization

### Changing the Schedule

To change how often the Lambda function runs, modify the `ScheduleExpression` property in the `template.yaml` file:

```yaml
LuxMedSniperScheduleRule:
  Type: AWS::Events::Rule
  Properties:
    Name: LuxMedSniperScheduleRule
    Description: 'Rule to trigger LuxMed Sniper Lambda every 60 seconds'
    ScheduleExpression: 'rate(1 minute)'  # Change this value
    # ...
```

### Changing the Region

To deploy to a different AWS region, modify the `REGION` variable in the `deploy.sh` script:

```bash
REGION="eu-west-1"  # Change to your preferred region
```

## Troubleshooting

### Lambda Function Timeout

If the Lambda function times out, you can increase the timeout value in the `template.yaml` file:

```yaml
LuxMedSniperLambdaFunction:
  Type: AWS::Lambda::Function
  Properties:
    # ...
    Timeout: 30  # Increase this value (in seconds)
    # ...
```

### Memory Issues

If the Lambda function runs out of memory, you can increase the memory allocation in the `template.yaml` file:

```yaml
LuxMedSniperLambdaFunction:
  Type: AWS::Lambda::Function
  Properties:
    # ...
    MemorySize: 256  # Increase this value (in MB)
    # ...
```

### Deployment Failures

If the deployment fails, check the CloudFormation events in the AWS Management Console:

1. Go to the CloudFormation service
2. Select the "LuxMedSniperStack" stack
3. Check the "Events" tab to see what went wrong

### Package Size Limitations

AWS Lambda has a deployment package size limit of 50 MB (zipped) and 250 MB (unzipped). If your package exceeds these limits, you might need to:

1. Remove unnecessary dependencies
2. Optimize your code and dependencies
3. Consider using Lambda layers (a more advanced approach) 