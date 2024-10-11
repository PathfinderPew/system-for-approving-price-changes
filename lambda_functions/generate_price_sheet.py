import boto3
import json
import os

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table_name = os.getenv('DYNAMODB_TABLE', 'PricingProposals')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    """Lambda function to generate a pricing sheet document."""
    # Expected event format:
    # {
    #   "proposals": [
    #       {"competitor_url": "<some_url>", "competitor_product_id": "<some_id>", "competitor_price": <some_price>, "internal_product_id": "<your_product_id>", "current_price": <current_price>}
    #   ]
    # }
    
    # Extract proposals from the event
    proposals = event.get('proposals', [])
    
    if not proposals:
        return {"statusCode": 400, "body": json.dumps("No pricing proposals provided.")}

    # Create entries in the PricingProposals table
    for proposal in proposals:
        item = {
            'ProductID': str(proposal['internal_product_id']),
            'VariantID': str(proposal['competitor_product_id']),
            'CompetitorURL': proposal['competitor_url'],
            'CurrentPrice': float(proposal['current_price']),
            'CompetitorPrice': float(proposal['competitor_price']),
            'ProposedPrice': float(min(proposal['current_price'], proposal['competitor_price'])),
            'ApprovalStatus': 'Pending',
            'ReviewedBy': 'None'
        }

        # Write to DynamoDB table
        table.put_item(Item=item)
    
    return {"statusCode": 200, "body": json.dumps("Pricing sheet generated and stored successfully.")}
