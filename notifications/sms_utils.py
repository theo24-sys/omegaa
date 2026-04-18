import africastalking
from django.conf import settings
import logging
import re

logger = logging.getLogger(__name__)

# Initialize Africa's Talking
# SECURITY: Require explicit configuration - don't use defaults in production
username = getattr(settings, 'AFRICASTALKING_USERNAME', '')
api_key = getattr(settings, 'AFRICASTALKING_API_KEY', '')

if not username and not settings.DEBUG:
    logger.warning("AFRICASTALKING_USERNAME not set. SMS will be disabled in production.")

if api_key:
    africastalking.initialize(username or 'sandbox', api_key)
    sms = africastalking.SMS
else:
    sms = None
    logger.warning("AFRICASTALKING_API_KEY not found. SMS will not be sent.")


def normalize_phone_for_sms(phone):
    """
    Normalize phone number for SMS sending (Africa's Talking format)
    Returns phone in +254XXXXXXXXX format
    """
    # Remove spaces/dashes
    p = ''.join(filter(str.isdigit, phone))
    
    if p.startswith('0'):
        p = '+254' + p[1:]
    elif p.startswith('7') or p.startswith('1'):
        p = '+254' + p
    elif not p.startswith('+254'):
        p = '+254' + p
    
    return p


def send_sms(to, message):
    """
    Sends an SMS using Africa's Talking.
    'to' can be a single phone number or a list.
    Automatically formats Kenyan numbers to +254.
    """
    if not sms:
        logger.error("SMS service not initialized. Check AFRICASTALKING credentials.")
        return False

    # Format phone numbers
    if isinstance(to, str):
        recipients = [to]
    else:
        recipients = to

    formatted_recipients = []
    for phone in recipients:
        normalized = normalize_phone_for_sms(phone)
        if normalized:
            formatted_recipients.append(normalized)

    if not formatted_recipients:
        logger.error(f"No valid phone numbers to send SMS to: {recipients}")
        return False

    try:
        response = sms.send(message, formatted_recipients)
        logger.info(f"SMS sent to {len(formatted_recipients)} recipients")
        return response
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}", exc_info=True)
        return False
