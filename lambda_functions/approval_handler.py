import json
import boto3
import os

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table_name = os.getenv('DYNAMODB_TABLE', 'PricingProposals')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    """
    Lambda function to handle approval or rejection of proposed price changes.
    Expects the following JSON input:
    {
      "action": "approve" or "reject",
      "product_id": "<ProductID>",
      "variant_id": "<VariantID>",
      "reviewer": "<Reviewer Name>"
    }
    """

    # Parse the input from the HTTP request body
    body = json.loads(event.get("body", "{}"))
    action = body.get('action')
    product_id = body.get('product_id')
    variant_id = body.get('variant_id')
    reviewer = body.get('reviewer', 'Unknown')

    # Validate required fields
    if not action or not product_id or not variant_id:
        return {
            "statusCode": 400,
            "body": json.dumps("Missing required fields: 'action', 'product_id', and 'variant_id'.")
        }

    # Determine the new approval status based on the action
    if action == "approve":
        new_status = "Approved"
    elif action == "reject":
        new_status = "Rejected"
    else:
        return {
            "statusCode": 400,
            "body": json.dumps(f"Invalid action: {action}. Allowed values are 'approve' or 'reject'.")
        }

    # Update the DynamoDB table entry for the specified product and variant
    try:
        response = table.update_item(
            Key={
                'ProductID': product_id,
                'VariantID': variant_id
            },
            UpdateExpression="SET ApprovalStatus = :status, ReviewedBy = :reviewer",
            ExpressionAttributeValues={
                ':status': new_status,
                ':reviewer': reviewer
            },
            ReturnValues="UPDATED_NEW"
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"Price change for Product {product_id} (Variant {variant_id}) has been {new_status.lower()} by {reviewer}.",
                "updatedAttributes": response['Attributes']
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error updating item: {e}")
        }
