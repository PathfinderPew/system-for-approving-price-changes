import boto3
import json
import os

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table_name = os.getenv('DYNAMODB_TABLE', 'PricingProposals')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    """
    Lambda function to get a product by ProductID and VariantID from the PricingProposals table.
    Expects the following parameters in the event's path:
    - product_id: The ID of the product
    - variant_id: The ID of the variant (optional, if variants are applicable)
    """

    try:
        # Extract product_id and variant_id from the event pathParameters
        product_id = event['pathParameters'].get('product_id')
        variant_id = event['pathParameters'].get('variant_id')

        # Validate required fields
        if not product_id or not variant_id:
            return {
                "statusCode": 400,
                "body": json.dumps("Missing required fields: 'product_id' and 'variant_id'.")
            }

        # Fetch the product from DynamoDB
        response = table.get_item(
            Key={
                'ProductID': product_id,
                'VariantID': variant_id
            }
        )

        # Check if the product was found
        if 'Item' not in response:
            return {
                "statusCode": 404,
                "body": json.dumps(f"Product with ID {product_id} and Variant {variant_id} not found.")
            }

        # Return the product details
        return {
            "statusCode": 200,
            "body": json.dumps(response['Item'])
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error retrieving product: {str(e)}")
        }
