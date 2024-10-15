import boto3
import json
import os

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table_name = os.getenv('DYNAMODB_TABLE', 'PricingProposals')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    """
    Lambda function to get all products with price changes pending approval.
    """

    try:
        # Scan the DynamoDB table to fetch items with ApprovalStatus as "Pending"
        response = table.scan(
            FilterExpression="ApprovalStatus = :status",
            ExpressionAttributeValues={":status": "Pending"}
        )

        # Return the list of products that are pending approval
        return {
            "statusCode": 200,
            "body": json.dumps(response.get('Items', []))
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error retrieving products: {str(e)}")
        }
