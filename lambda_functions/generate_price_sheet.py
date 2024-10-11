import boto3
import json
import os

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table_name = os.getenv('DYNAMODB_TABLE', 'PricingProposals')
table = dynamodb.Table(table_name)

# Assume there's a separate table for minimum prices
min_price_table_name = os.getenv('MIN_PRICE_TABLE', 'MinimumPrices')
min_price_table = dynamodb.Table(min_price_table_name)

def get_minimum_price(internal_product_id):
    """Fetch the minimum price for a given product from the minimum prices table."""
    try:
        response = min_price_table.get_item(Key={'ProductID': internal_product_id})
        return float(response['Item']['MinimumPrice'])
    except Exception as e:
        print(f"Error fetching minimum price for Product {internal_product_id}: {e}")
        return None

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
        internal_product_id = proposal['internal_product_id']
        competitor_price = float(proposal['competitor_price'])
        current_price = float(proposal['current_price'])

        # Fetch the minimum price for this product
        min_price = get_minimum_price(internal_product_id)

        if min_price is None:
            return {"statusCode": 500, "body": json.dumps(f"Error retrieving minimum price for Product ID {internal_product_id}.")}

        # Only mark for approval if competitor price is lower than current price but higher than the minimum price
        if competitor_price < current_price and competitor_price >= min_price:
            proposed_price = competitor_price
        else:
            proposed_price = current_price

        item = {
            'ProductID': str(internal_product_id),
            'VariantID': str(proposal['competitor_product_id']),
            'CompetitorURL': proposal['competitor_url'],
            'CurrentPrice': current_price,
            'CompetitorPrice': competitor_price,
            'ProposedPrice': proposed_price,
            'ApprovalStatus': 'Pending',
            'ReviewedBy': 'None'
        }

        # Write to DynamoDB table
        table.put_item(Item=item)

    return {"statusCode": 200, "body": json.dumps("Pricing sheet generated and stored successfully.")}
