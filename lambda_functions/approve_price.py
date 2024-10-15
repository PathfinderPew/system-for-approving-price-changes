import boto3
import json
import os

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table_name = os.getenv('DYNAMODB_TABLE', 'PricingProposals')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    """
    Lambda function to approve a price change for a product.
    Expects the following parameters in the event body:
    - product_id: The ID of the product
    - variant_id: The ID of the variant (optional)
    - reviewer: The name of the person approving the price
    """

    try:
        # Parse the request body
        body = json.loads(event['body'])
        product_id = body.get('product_id')
        variant_id = body.get('variant_id')
        reviewer = body.get('reviewer', 'Unknown')

        # Validate required fields
        if not product_id or not variant_id:
            return {
                "statusCode": 400,
                "body": json.dumps("Missing required fields: 'product_id' and 'variant_id'.")
            }

        # Update the DynamoDB table to mark the price as approved
        response = table.update_item(
            Key={
                'ProductID': product_id,
                'VariantID': variant_id
            },
            UpdateExpression="SET ApprovalStatus = :status, ReviewedBy = :reviewer",
            ExpressionAttributeValues={
                ':status': 'Approved',
                ':reviewer': reviewer
            },
            ReturnValues="UPDATED_NEW"
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"Price change for Product {product_id} (Variant {variant_id}) has been approved.",
                "updatedAttributes": response['Attributes']
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error approving price: {str(e)}")
        }
