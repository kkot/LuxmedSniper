import os
import sys
import json
import logging
from luxmed_sniper import setup_logging, work

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
        
        # Run the script with the --once flag
        work(config_files)
        
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