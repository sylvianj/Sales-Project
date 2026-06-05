
import re

def format_phone_number(phone):
    """Convert a phone number to the format 2547XXXXXXXX."""
    # Remove any non-digit characters
    phone = re.sub(r'\D', '', phone)
    
    # Remove leading '0' or '+254' to add the correct prefix
    if phone.startswith('0'):
        phone = phone[1:]
    elif phone.startswith('254'):
        phone = phone[3:]
    elif phone.startswith('+254'):
        phone = phone[4:]
    
    # Prepend '254' and ensure it's 12 digits long
    return f"254{phone}"