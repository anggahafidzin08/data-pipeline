import logging
from typing import Optional, Tuple
import re

logger = logging.getLogger(__name__)

class Validator:
    """Validate product data fields."""

    @staticmethod
    def validate_price(price: Optional[float]) -> Tuple[bool, Optional[str]]:
        """Validate price is numeric and in reasonable range."""
        if price is None:
            return False, "Price is required"

        try:
            p = float(price)
            if p < 0.01 or p > 1_000_000:
                return False, f"Price {p} out of range [0.01, 1,000,000]"
            return True, None
        except (ValueError, TypeError):
            return False, f"Price is not numeric: {price}"

    @staticmethod
    def validate_product_name(name: Optional[str]) -> Tuple[bool, Optional[str]]:
        """Validate product name is non-empty."""
        if not name or not name.strip():
            return False, "Product name is required"
        return True, None

    @staticmethod
    def validate_url(url: Optional[str]) -> Tuple[bool, Optional[str]]:
        """Validate URL format."""
        if not url:
            return True, None  # URL is optional

        if not re.match(r'^https?://', url):
            return False, f"Invalid URL format: {url}"
        return True, None

class ValidationResult:
    """Hold validation result."""

    def __init__(self):
        self.errors = []
        self.status = "PASS"

    def add_error(self, message: str):
        self.errors.append(message)
        self.status = "FAIL"

    def add_warning(self, message: str):
        if self.status != "FAIL":
            self.status = "WARN"
        self.errors.append(f"WARNING: {message}")

    def __str__(self):
        return "; ".join(self.errors) if self.errors else ""
