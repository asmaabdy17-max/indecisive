import logging
from typing import Optional, Dict, List, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote

from .base_scraper import BaseScraper
from config.settings import Settings
from storage.database import Database
from utils.normalizers import (
    normalize_phone, normalize_address, extract_locality,
    extract_email, normalize_category
)
from utils.validators import is_valid_phone

logger = logging.getLogger(__name__)


class SulkhaScraper(BaseScraper):
    """Scraper for Sulekha.com listings."""

    def __init__(self, settings: Settings, database: Database):
        super().__init__(settings, database)
        self.base_url = settings.platforms["sulekha"]["base_url"]
        self.platform = "sulekha"

    async def discover_categories(self) -> List[str]:
        """Discover categories from Sulekha."""
        logger.info("Discovering Sulekha categories")

        categories = []
        try:
            response = await self.http_client.get(f"{self.base_url}/bangalore")

            if response:
                soup = BeautifulSoup(response.content, "html.parser")
                category_links = soup.find_all("a", href=True)

                for link in category_links[:20]:
                    text = link.get_text(strip=True)
                    if any(keyword in text.lower() for keyword in ["teacher", "class", "tuition", "coaching"]):
                        categories.append(normalize_category(text))

        except Exception as e:
            logger.error(f"Error discovering categories: {str(e)}")
            self._save_error(f"{self.base_url}/bangalore", "category_discovery", str(e))

        return categories

    async def discover_listings(self, category: str, locality: str) -> List[str]:
        """Discover listing URLs from search results."""
        logger.info(f"Discovering listings for {category} in {locality}")

        listing_urls = []

        try:
            search_query = f"{category} in {locality}"
            search_url = f"{self.base_url}/search?q={quote(search_query)}"

            response = await self.http_client.get(search_url)

            if response:
                soup = BeautifulSoup(response.content, "html.parser")
                listing_divs = soup.find_all("div", class_="resultbox")

                for div in listing_divs[:100]:
                    link = div.find("a", href=True)
                    if link:
                        url = urljoin(self.base_url, link["href"])
                        if url not in listing_urls:
                            listing_urls.append(url)

        except Exception as e:
            logger.error(f"Error discovering listings: {str(e)}")
            self._save_error(search_url, "listing_discovery", str(e))

        return listing_urls

    async def extract_listing_details(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract details from individual listing."""
        try:
            response = await self.http_client.get(url)

            if not response:
                return None

            soup = BeautifulSoup(response.content, "html.parser")

            provider_name = self._extract_name(soup)
            if not provider_name:
                return None

            phone_numbers = self._extract_phones(soup)
            email = self._extract_email(soup)
            address = self._extract_address(soup)

            return {
                "provider_id": self._extract_id_from_url(url),
                "listing_url": url,
                "provider_name": provider_name,
                "description": self._extract_description(soup),
                "phone_number": phone_numbers[0] if phone_numbers else None,
                "whatsapp_number": phone_numbers[1] if len(phone_numbers) > 1 else None,
                "email": email,
                "full_address": address,
                "locality": extract_locality(address),
                "city": "Bangalore",
                "website": self._extract_website(soup),
                "rating": self._extract_rating(soup),
                "review_count": self._extract_review_count(soup),
                "category": "teacher",
                "image_urls": self._extract_images(soup),
            }

        except Exception as e:
            logger.error(f"Error extracting listing {url}: {str(e)}")
            self._save_error(url, "parse_error", str(e))
            return None

    def _extract_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract provider name."""
        name_elem = soup.find("h1", class_="profname")
        return name_elem.get_text(strip=True) if name_elem else None

    def _extract_phones(self, soup: BeautifulSoup) -> List[str]:
        """Extract phone numbers."""
        phones = []
        phone_elems = soup.find_all("span", class_="phonenumber")
        for elem in phone_elems:
            phone = elem.get_text(strip=True)
            normalized = normalize_phone(phone)
            if normalized and is_valid_phone(normalized) and normalized not in phones:
                phones.append(normalized)
        return phones

    def _extract_email(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract email."""
        email_elem = soup.find("span", class_="email")
        return email_elem.get_text(strip=True) if email_elem else None

    def _extract_address(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract address."""
        address_elem = soup.find("div", class_="address")
        if address_elem:
            return normalize_address(address_elem.get_text())
        return None

    def _extract_website(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract website URL."""
        website_elem = soup.find("a", class_="website")
        return website_elem.get("href") if website_elem else None

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract business description."""
        desc_elem = soup.find("div", class_="description")
        return desc_elem.get_text(strip=True) if desc_elem else None

    def _extract_rating(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract rating."""
        rating_elem = soup.find("span", class_="rating-value")
        if rating_elem:
            try:
                return float(rating_elem.get_text(strip=True))
            except (ValueError, AttributeError):
                return None
        return None

    def _extract_review_count(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract review count."""
        review_elem = soup.find("span", class_="reviews-count")
        if review_elem:
            try:
                return int(review_elem.get_text(strip=True).split()[0])
            except (ValueError, AttributeError):
                return None
        return None

    def _extract_images(self, soup: BeautifulSoup) -> Optional[List[str]]:
        """Extract image URLs."""
        images = []
        img_elements = soup.find_all("img", class_="thumbnail")
        for img in img_elements[:5]:
            src = img.get("src")
            if src:
                images.append(src)
        return images if images else None

    @staticmethod
    def _extract_id_from_url(url: str) -> str:
        """Extract provider ID from URL."""
        return url.split("/")[-1].split("?")[0]
