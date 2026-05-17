import re
import hashlib
import phonenumbers
from typing import Optional, Tuple
from fuzzywuzzy import fuzz


BANGALORE_LOCALITIES = {
    "whitefield", "hsr layout", "bellandur", "sarjapur", "marathahalli",
    "koramangala", "indiranagar", "jayanagar", "electronic city", "yelahanka",
    "jp nagar", "btm layout", "hebbal", "bannerghatta", "cv raman nagar",
    "brookefield", "rr nagar", "rajajinagar", "malleshwaram",
}

CATEGORY_MAPPINGS = {
    "music": "music_teacher",
    "dance": "dance_classes",
    "sports": "sports_coaching",
    "swimming": "swimming",
    "martial arts": "martial_arts",
    "yoga": "yoga",
    "chess": "chess",
    "coding": "coding_classes",
    "english": "spoken_english",
    "language": "language_tutors",
    "tuition": "home_tuition",
    "art": "art_craft",
    "pottery": "pottery",
    "robotics": "robotics",
    "abacus": "abacus",
    "public speaking": "public_speaking",
    "daycare": "daycare",
    "babysitting": "babysitting",
    "personality": "personality_development",
    "exam coaching": "competitive_exam_coaching",
    "kids": "kids_activities",
    "hobby": "hobby_classes",
}


def normalize_phone(phone: Optional[str]) -> Optional[str]:
    """Normalize phone number to +91XXXXXXXXXX format."""
    if not phone:
        return None

    phone = re.sub(r"\D", "", phone)

    if len(phone) == 10:
        return f"+91{phone}"
    elif len(phone) == 12 and phone.startswith("91"):
        return f"+{phone}"
    elif len(phone) == 13 and phone.startswith("+91"):
        return phone
    elif len(phone) == 11 and phone.startswith("0"):
        return f"+91{phone[1:]}"

    return phone if len(phone) >= 10 else None


def normalize_address(address: Optional[str]) -> Optional[str]:
    """Normalize address by removing extra spaces and special chars."""
    if not address:
        return None

    address = re.sub(r"\s+", " ", address).strip()
    address = re.sub(r"[^\w\s\-,.]", " ", address)
    address = re.sub(r"\s+", " ", address).strip()

    return address


def extract_locality(address: Optional[str], locality_list: Optional[list] = None) -> Optional[str]:
    """Extract locality from address using fuzzy matching."""
    if not address:
        return None

    address_lower = address.lower()
    localities = locality_list or BANGALORE_LOCALITIES

    for locality in localities:
        if locality in address_lower:
            return locality.title()

        if fuzz.token_set_ratio(locality, address_lower) > 85:
            return locality.title()

    return None


def normalize_category(category: Optional[str]) -> Optional[str]:
    """Normalize category name to standard slugs."""
    if not category:
        return None

    category_lower = category.lower()

    for key, value in CATEGORY_MAPPINGS.items():
        if key in category_lower:
            return value

    return category_lower.replace(" ", "_")


def calculate_hash(
    source_platform: str,
    provider_name: str,
    phone_number: Optional[str] = None,
    email: Optional[str] = None,
) -> str:
    """Calculate MD5 hash for deduplication."""
    data = f"{source_platform}:{provider_name}:{phone_number or ''}:{email or ''}"
    return hashlib.md5(data.encode()).hexdigest()


def extract_email(text: Optional[str]) -> Optional[str]:
    """Extract email from text."""
    if not text:
        return None

    emails = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
    return emails[0] if emails else None


def extract_phone_numbers(text: Optional[str]) -> list:
    """Extract all phone numbers from text."""
    if not text:
        return []

    phones = []
    phone_pattern = r"(?:\+91|0)?[789]\d{9}"
    matches = re.findall(phone_pattern, text)

    for match in matches:
        normalized = normalize_phone(match)
        if normalized and normalized not in phones:
            phones.append(normalized)

    return phones


def extract_urls(text: Optional[str]) -> list:
    """Extract URLs from text."""
    if not text:
        return []

    url_pattern = r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)"
    return re.findall(url_pattern, text)


def extract_social_handles(text: Optional[str]) -> dict:
    """Extract social media handles from text."""
    if not text:
        return {}

    handles = {}

    instagram_match = re.search(r"(?:instagram\.com/)?(@?[a-zA-Z0-9_.]+)", text)
    if instagram_match:
        handles["instagram"] = instagram_match.group(1).lstrip("@")

    facebook_match = re.search(r"facebook\.com/[\w-]+", text)
    if facebook_match:
        handles["facebook"] = facebook_match.group(0)

    youtube_match = re.search(r"youtube\.com/(?:c|channel)/[\w-]+", text)
    if youtube_match:
        handles["youtube"] = youtube_match.group(0)

    return handles


def calculate_data_quality_score(provider_data: dict) -> float:
    """Calculate data quality score (0-1) based on field completeness."""
    required_fields = [
        "provider_name", "phone_number", "city", "locality",
        "category", "description"
    ]
    optional_fields = [
        "rating", "email", "website", "image_urls", "years_experience",
        "languages_spoken", "subjects_taught"
    ]

    required_score = sum(1 for field in required_fields if provider_data.get(field))
    optional_score = sum(1 for field in optional_fields if provider_data.get(field))

    total_score = (required_score / len(required_fields)) * 0.7
    total_score += (optional_score / len(optional_fields)) * 0.3

    return min(1.0, total_score)
