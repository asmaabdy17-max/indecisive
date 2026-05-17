import re
import validators
from typing import Optional
import phonenumbers


def is_valid_phone(phone: Optional[str]) -> bool:
    """Check if phone number is valid Indian number."""
    if not phone:
        return False

    try:
        parsed = phonenumbers.parse(phone, "IN")
        return phonenumbers.is_valid_number(parsed)
    except (phonenumbers.NumberParseException, Exception):
        phone_clean = re.sub(r"\D", "", str(phone))
        return len(phone_clean) == 10 or (len(phone_clean) == 12 and phone_clean.startswith("91"))


def is_valid_email(email: Optional[str]) -> bool:
    """Check if email is valid."""
    if not email:
        return False

    return bool(validators.email(email))


def is_valid_url(url: Optional[str]) -> bool:
    """Check if URL is valid."""
    if not url:
        return False

    return bool(validators.url(url))


def is_valid_pincode(pincode: Optional[str]) -> bool:
    """Check if Indian pincode is valid."""
    if not pincode:
        return False

    pincode = re.sub(r"\D", "", str(pincode))
    return len(pincode) == 6 and pincode.isdigit()


def is_valid_address(address: Optional[str]) -> bool:
    """Check if address has minimum required length."""
    if not address:
        return False

    return len(address.strip()) >= 5


def contains_captcha_keywords(text: Optional[str]) -> bool:
    """Check if text contains CAPTCHA-related keywords."""
    if not text:
        return False

    keywords = ["captcha", "verify", "robot", "suspicious", "unusual activity"]
    text_lower = text.lower()

    return any(keyword in text_lower for keyword in keywords)
