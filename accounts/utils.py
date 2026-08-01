"""
Utility functions for accounts app
"""
import re
import logging

logger = logging.getLogger(__name__)


def normalize_kenyan_phone(phone):
    """
    Normalize Kenyan phone number to 254XXXXXXXXX format
    
    Accepts formats:
    - 0712345678
    - 254712345678
    - +254712345678
    - 712345678
    
    Args:
        phone: Phone number as string
        
    Returns:
        Normalized phone number (254XXXXXXXXX) or None if invalid
    """
    if not phone:
        return None
    
    # Remove spaces, dashes, parentheses
    phone = re.sub(r'[\s\-\(\)]+', '', str(phone))
    
    # Remove leading +
    if phone.startswith('+'):
        phone = phone[1:]
    
    # If starts with 0, replace with 254
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    
    # If doesn't start with 254, try adding it
    elif not phone.startswith('254'):
        phone = '254' + phone
    
    # Validate: Should be exactly 12 digits (254 + 9 digit Safaricom number)
    if not re.match(r'^254[17]\d{8}$', phone):
        logger.warning(f"Invalid Kenyan phone format after normalization: {phone}")
        return None
    
    return phone


def validate_kenyan_phone(phone):
    """
    Validate if phone number is a valid Kenyan number
    
    Args:
        phone: Phone number as string
        
    Returns:
        bool: True if valid, False otherwise
    """
    normalized = normalize_kenyan_phone(phone)
    return normalized is not None
