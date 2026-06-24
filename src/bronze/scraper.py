import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from src.common.config import get_settings
from src.common.utils import calculate_hash
from datetime import datetime

logger = logging.getLogger(__name__)

class Scraper:
    """Web scraper for e-commerce products."""

    def __init__(self, source_url: Optional[str] = None):
        settings = get_settings()
        self.source_url = source_url or settings.source_url
        self.source_id = settings.source_id
        self.timeout = settings.scraper.get("timeout_seconds", 30)
        self.retry_attempts = settings.scraper.get("retry_attempts", 2)
        self.delay = settings.scraper.get("delay_between_requests", 1)

    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape products from source and return raw data."""
        products = []
        current_url = self.source_url
        page_count = 0

        while current_url and page_count < 100:  # Safety limit
            try:
                logger.info(f"Scraping: {current_url}")
                response = self._fetch_url(current_url)

                if response.status_code != 200:
                    logger.error(f"Failed to fetch {current_url}: {response.status_code}")
                    break

                soup = BeautifulSoup(response.content, "html.parser")
                page_products = self._extract_products(soup)
                products.extend(page_products)
                logger.info(f"Found {len(page_products)} products on page {page_count + 1}")

                # Get next page link
                next_link = soup.find("a", {"aria-label": "Next"})
                if next_link and "href" in next_link.attrs:
                    next_href = next_link["href"]
                    if next_href.startswith("http"):
                        current_url = next_href
                    else:
                        current_url = self.source_url + next_href
                else:
                    current_url = None

                page_count += 1

            except Exception as e:
                logger.error(f"Error scraping: {e}")
                break

        logger.info(f"Scraping complete. Total products: {len(products)}")
        return products

    def _fetch_url(self, url: str) -> requests.Response:
        """Fetch URL with retries."""
        for attempt in range(self.retry_attempts):
            try:
                response = requests.get(url, timeout=self.timeout)
                return response
            except requests.RequestException as e:
                if attempt == self.retry_attempts - 1:
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")

        raise requests.RequestException(f"Failed after {self.retry_attempts} attempts")

    def _extract_products(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract product data from HTML."""
        products = []

        # Find all product cards
        product_elements = soup.find_all("div", class_="thumbnail")

        for elem in product_elements:
            try:
                # Extract fields
                title_elem = elem.find("a", class_="title")
                brand = title_elem.get("title") if title_elem else None

                price_elem = elem.find("h4", class_="price")
                price = price_elem.text.strip() if price_elem else None

                # Try to extract currency, default to None if not found
                currency = None
                if price_elem:
                    currency_elem = price_elem.find("meta", itemprop="priceCurrency")
                    currency = currency_elem.get("content") if currency_elem else None

                desc_elem = elem.find("p", class_="description")
                spec = desc_elem.text.strip() if desc_elem else None

                if brand:
                    # Generate composite_key from brand (normalized)
                    composite_key = brand.lower().replace(" ", "_").replace(".", "")

                    product_data = {
                        "brand": brand,
                        "price": price,
                        "currency": currency,
                        "spec": spec
                    }

                    products.append({
                        "composite_key": composite_key,
                        "raw_data": product_data,
                        "scraped_at": datetime.utcnow().isoformat() + "Z"
                    })

            except Exception as e:
                logger.warning(f"Failed to extract product: {e}")
                continue

        return products
