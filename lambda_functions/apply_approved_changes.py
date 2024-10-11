import json
import boto3
import os

# Import platform-specific update functions from the Pricing Integration Framework
from pricing_integration.shopify_api import update_product_price as update_shopify_price
from pricing_integration.netsuite_api import update_product_price as update_netsuite_price
from pricing_integration.zoey_api import update_product_price as update_zoey_price

# Initialize the DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table_name = os.getenv('DYNAMODB_TABLE', 'PricingProposals')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    """
    Lambda function to apply price changes for products marked as 'Approved' in DynamoDB.
    Uses the Pricing Integration Framework to update prices in Shopify, NetSuite, and Zoey.
    """
    # Scan the DynamoDB table for items with ApprovalStatus = "Approved"
    try:
        response = table.scan(
            FilterExpression="ApprovalStatus = :status",
            ExpressionAttributeValues={":status": "Approved"}
        )
    except Exception as e:
        print(f"Error scanning DynamoDB table: {e}")
        return {"statusCode": 500, "body": json.dumps("Error scanning DynamoDB table.")}

    # Process each approved item
    approved_items = response.get('Items', [])
    for item in approved_items:
        try:
            product_id = item['ProductID']
            variant_id = item['VariantID']
            proposed_price = item['ProposedPrice']
            platform = item.get('Platform', 'shopify')  # Assuming a Platform field specifies where to update

            # Call the appropriate function from the Integration Framework
            if platform == "shopify":
                success = update_shopify_price(product_id, variant_id, proposed_price)
            elif platform == "netsuite":
                success = update_netsuite_price(product_id, variant_id, proposed_price)
            elif platform == "zoey":
                success = update_zoey_price(product_id, variant_id, proposed_price)
            else:
                print(f"Unknown platform for Product {product_id}. Skipping update.")
                continue

            # If the price update was successful, mark the DynamoDB entry as "Completed"
            if success:
                table.update_item(
                    Key={
                        'ProductID': product_id,
                        'VariantID': variant_id
                    },
                    UpdateExpression="SET ApprovalStatus = :status",
                    ExpressionAttributeValues={":status": "Completed"}
                )
                print(f"Successfully updated price for Product {product_id} in {platform} and marked as Completed.")
            else:
                print(f"Failed to update price for Product {product_id} in {platform}. Retrying...")

        except Exception as e:
            print(f"Error applying price change for Product {product_id}: {e}")

    return {"statusCode": 200, "body": json.dumps("Approved price changes applied successfully.")}
