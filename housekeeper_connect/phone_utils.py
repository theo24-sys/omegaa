import re

def normalize_kenyan_phone(phone):
    """
    Standardizes Kenyan phone numbers to the 254XXXXXXXXX format.
    Handles:
    - 07XXXXXXXX -> 2547XXXXXXXX
    - +254XXXXXXXXX -> 254XXXXXXXXX
    - 254XXXXXXXXX -> 254XXXXXXXXX
    - 7XXXXXXXX -> 2547XXXXXXXX
    
    Returns: String in 254 format or None if invalid
    """
    if not phone:
        return None
        
    # Remove all non-numeric characters
    clean = re.sub(r'[^0-9]', '', str(phone))
    
    if clean.startswith('0'):
        # 07... -> 2547...
        if len(clean) == 10:
            return '254' + clean[1:]
    elif clean.startswith('254'):
        # 2547...
        if len(clean) == 12:
            return clean
    elif len(clean) == 9:
        # 7... -> 2547...
        return '254' + clean
        
    # If we can't normalize it, return None or consider it invalid
    return None
