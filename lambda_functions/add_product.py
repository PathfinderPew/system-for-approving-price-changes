import boto3
import json
import os

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table_name = os.getenv('DYNAMODB_TABLE', 'PricingProposals')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    """
    Lambda function to add a product to the PricingProposals table.
    Expects the following JSON input in the request body:
    {
      "product_id": "<ProductID>",
      "variant_id": "<VariantID>",
      "competitor_url": "<CompetitorURL>",
      "current_price": <CurrentPrice>,
      "competitor_price": <CompetitorPrice>,
      "proposed_price": <ProposedPrice>
    }
    """

    try:
        # Parse the input from the HTTP request body
        body = json.loads(event.get("body", "{}"))
        product_id = body.get('product_id')
        variant_id = body.get('variant_id')
        competitor_url = body.get('competitor_url')
        current_price = body.get('current_price')
        competitor_price = body.get('competitor_price')
        proposed_price = body.get('proposed_price')

        # Validate required fields
        if not all([product_id, variant_id, current_price, competitor_price, proposed_price]):
            return {
                "statusCode": 400,
                "body": json.dumps("Missing required fields.")
            }

        # Create the item to be added to the DynamoDB table
        item = {
            'ProductID': product_id,
            'VariantID': variant_id,
            'CompetitorURL': competitor_url,
            'CurrentPrice': float(current_price),
            'CompetitorPrice': float(competitor_price),
            'ProposedPrice': float(proposed_price),
            'ApprovalStatus': 'Pending',
            'ReviewedBy': 'None'
        }

        # Write the item to DynamoDB
        table.put_item(Item=item)

        return {
            "statusCode": 200,
            "body": json.dumps(f"Product {product_id} added successfully.")
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error adding product: {str(e)}")
        }
