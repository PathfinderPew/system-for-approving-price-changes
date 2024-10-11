import boto3
import os
import json

# Initialize the SES client
ses = boto3.client('ses', region_name='us-east-1')

# Get environment variables
SENDER_EMAIL = os.getenv('SES_SENDER_EMAIL', 'no-reply@yourdomain.com')
APPROVAL_EMAIL_LIST = os.getenv('APPROVAL_EMAIL_LIST', 'manager@example.com,manager2@example.com')

def lambda_handler(event, context):
    """
    Lambda function to send email notifications when a new pricing proposal is added or updated.
    Triggered by DynamoDB Streams.
    """

    # Parse through DynamoDB stream events
    for record in event['Records']:
        if record['eventName'] == 'INSERT':
            # New item added to the PricingProposals table
            new_image = record['dynamodb']['NewImage']
            send_proposal_notification(new_image)
        elif record['eventName'] == 'MODIFY':
            # Item in the PricingProposals table modified (could be approval or rejection)
            old_image = record['dynamodb']['OldImage']
            new_image = record['dynamodb']['NewImage']
            if old_image['ApprovalStatus']['S'] == "Pending" and new_image['ApprovalStatus']['S'] in ["Approved", "Rejected"]:
                send_approval_status_notification(new_image)

    return {"statusCode": 200, "body": json.dumps("Notifications processed successfully.")}

def send_proposal_notification(new_image):
    """
    Send an email notification for a new pricing proposal.
    """
    product_id = new_image['ProductID']['S']
    current_price = new_image['CurrentPrice']['N']
    competitor_price = new_image['CompetitorPrice']['N']
    proposed_price = new_image['ProposedPrice']['N']
    approval_status = new_image['ApprovalStatus']['S']

    # Create the email subject and body
    subject = f"New Pricing Proposal for Product {product_id}"
    body_text = (
        f"A new pricing proposal has been created:\n"
        f"Product ID: {product_id}\n"
        f"Current Price: {current_price}\n"
        f"Competitor Price: {competitor_price}\n"
        f"Proposed Price: {proposed_price}\n"
        f"Approval Status: {approval_status}\n"
        f"Please review the proposal in the Pricing Approval Dashboard."
    )

    # Send the email
    send_email(subject, body_text)


def send_approval_status_notification(new_image):
    """
    Send an email notification for a change in approval status.
    """
    product_id = new_image['ProductID']['S']
    variant_id = new_image['VariantID']['S']
    proposed_price = new_image['ProposedPrice']['N']
    approval_status = new_image['ApprovalStatus']['S']
    reviewed_by = new_image.get('ReviewedBy', {}).get('S', 'Unknown')

    # Create the email subject and body
    subject = f"Pricing Proposal Update for Product {product_id}"
    body_text = (
        f"The pricing proposal for Product {product_id}, Variant {variant_id} has been {approval_status}.\n"
        f"Proposed Price: {proposed_price}\n"
        f"Reviewed By: {reviewed_by}\n"
        f"Approval Status: {approval_status}\n"
        f"Please review the status in the Pricing Approval Dashboard."
    )

    # Send the email
    send_email(subject, body_text)


def send_email(subject, body_text):
    """
    Helper function to send an email using SES.
    """
    try:
        # Send email using SES
        response = ses.send_email(
            Source=SENDER_EMAIL,
            Destination={
                'ToAddresses': APPROVAL_EMAIL_LIST.split(',')
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': body_text,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        print(f"Email sent successfully: {response['MessageId']}")
    except Exception as e:
        print(f"Error sending email: {e}")
