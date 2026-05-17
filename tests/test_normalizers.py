import pytest
from utils.normalizers import (
    normalize_phone,
    normalize_address,
    normalize_category,
    extract_locality,
    calculate_hash,
    is_valid_phone,
)


class TestPhoneNormalization:
    def test_10_digit_phone(self):
        assert normalize_phone("9876543210") == "+919876543210"

    def test_10_digit_with_prefix(self):
        assert normalize_phone("0-98-765-43210") == "+919876543210"

    def test_already_normalized(self):
        assert normalize_phone("+919876543210") == "+919876543210"

    def test_invalid_phone(self):
        assert normalize_phone("123") is None

    def test_none_phone(self):
        assert normalize_phone(None) is None


class TestAddressNormalization:
    def test_extra_spaces(self):
        result = normalize_address("123   Main St   Bangalore")
        assert "   " not in result

    def test_special_characters(self):
        result = normalize_address("123 Main St @ Bangalore")
        assert "@" not in result


class TestCategoryNormalization:
    def test_music_category(self):
        assert normalize_category("Music Teacher") == "music_teacher"

    def test_dance_category(self):
        assert normalize_category("Dance Classes") == "dance_classes"

    def test_unknown_category(self):
        result = normalize_category("Unknown Category")
        assert result == "unknown_category"


class TestLocalityExtraction:
    def test_exact_locality(self):
        assert extract_locality("123 Whitefield, Bangalore") == "Whitefield"

    def test_fuzzy_match(self):
        assert extract_locality("HSR Lay, Bangalore") == "Hsr Layout"

    def test_no_locality(self):
        assert extract_locality("123 Unknown Place") is None


class TestHash:
    def test_consistent_hash(self):
        hash1 = calculate_hash("justdial", "John Doe", "+919876543210")
        hash2 = calculate_hash("justdial", "John Doe", "+919876543210")
        assert hash1 == hash2

    def test_different_hash(self):
        hash1 = calculate_hash("justdial", "John Doe", "+919876543210")
        hash2 = calculate_hash("sulekha", "John Doe", "+919876543210")
        assert hash1 != hash2
