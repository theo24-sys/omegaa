import africastalking
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Africa's Talking
username = getattr(settings, 'AFRICASTALKING_USERNAME', 'sandbox')
api_key = getattr(settings, 'AFRICASTALKING_API_KEY', '')

if api_key:
    africastalking.initialize(username, api_key)
    sms = africastalking.SMS
else:
    sms = None
    logger.warning("AFRICASTALKING_API_KEY not found. SMS will not be sent.")

def send_sms(to, message):
    """
    Sends an SMS using Africa's Talking.
    'to' can be a single phone number or a list.
    Automatically formats Kenyan numbers to +254.
    """
    if not sms:
        logger.error("SMS service not initialized.")
        return False

    # Format phone numbers
    if isinstance(to, str):
        recipients = [to]
    else:
        recipients = to

    formatted_recipients = []
    for phone in recipients:
        # Remove spaces/dashes
        p = ''.join(filter(str.isdigit, phone))
        if p.startswith('0'):
            p = '+254' + p[1:]
        elif p.startswith('7') or p.startswith('1'):
            p = '+254' + p
        elif not p.startswith('+'):
            # Fallback/Unknown
            p = '+' + p
        formatted_recipients.append(p)

    try:
        response = sms.send(message, formatted_recipients)
        logger.info(f"SMS Response: {response}")
        return response
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        return False
