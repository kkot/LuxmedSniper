import os
import sys
import json
import logging
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from luxmed_sniper import FailureAlerts, LuxMedSniper, setup_logging, work

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")


def _state_files(config_files):
    """Files that must survive between invocations: the sent-notifications DB and the failure alert marker."""
    notifydb = Path(LuxMedSniper._load_configuration(config_files)["misc"]["notifydb"])
    return [notifydb, notifydb.with_name(FailureAlerts.MARKER_NAME)]


def _download_state(bucket, files):
    # Each invocation usually lands in a fresh container with an empty /tmp, so state lives in S3
    for path in files:
        try:
            s3.download_file(bucket, path.name, str(path))
        except ClientError as e:
            if e.response["Error"]["Code"] not in ("404", "NoSuchKey"):
                raise
            path.unlink(missing_ok=True)


def _upload_state(bucket, files):
    for path in files:
        if path.exists():
            s3.upload_file(str(path), bucket, path.name)
        else:
            s3.delete_object(Bucket=bucket, Key=path.name)


def handler(event, context):
    """
    AWS Lambda handler function that runs LuxMed Sniper with the --once flag.

    Args:
        event: AWS Lambda event data
        context: AWS Lambda context

    Returns:
        dict: Response with execution status
    """
    try:
        # Set up logging
        setup_logging()

        # Get configuration files from environment variables
        config_files = [
            os.environ.get('CONFIG_FILE', 'luxmed_sniper.yaml'),
            os.environ.get('ACCOUNT_FILE', 'account.yaml')
        ]

        # Log the execution
        logger.info(f"Running LuxMed Sniper with config files: {config_files}")

        state_bucket = os.environ.get('STATE_BUCKET')
        state_files = _state_files(config_files) if state_bucket else []
        if state_bucket:
            _download_state(state_bucket, state_files)

        # Run the script with the --once flag
        work(config_files)

        if state_bucket:
            _upload_state(state_bucket, state_files)

        return {
            'statusCode': 200,
            'body': json.dumps('LuxMed Sniper executed successfully')
        }
    except Exception as e:
        logger.error(f"Error executing LuxMed Sniper: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
