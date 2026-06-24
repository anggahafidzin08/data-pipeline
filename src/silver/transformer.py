import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.silver.parser import SpecParser
from src.silver.validators import Validator, ValidationResult
from src.common.utils import calculate_hash
from src.common.config import get_settings

logger = logging.getLogger(__name__)

class Transformer:
    """Transform and clean raw Bronze data into Silver layer."""

    def __init__(self):
        settings = get_settings()
        self.source_id = settings.source_id
        self.parser = SpecParser()
        self.validator = Validator()

    def transform(self, raw_products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform raw products into clean, validated records."""
        cleaned = []

        for raw_product in raw_products:
            try:
                clean_record = self._transform_single(raw_product)
                cleaned.append(clean_record)
            except Exception as e:
                logger.error(f"Failed to transform product: {e}")
                continue

        logger.info(f"Transformed {len(cleaned)} of {len(raw_products)} products")
        return cleaned

    def _transform_single(self, raw_product: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a single raw product."""

        raw_data = raw_product.get("raw_data", {})
        composite_key = raw_product.get("composite_key")
        source_hash = raw_product.get("hash_raw")

        # Extract raw fields
        brand = raw_data.get("brand", "").strip()
        price_str = raw_data.get("price", "")
        spec = raw_data.get("spec", "").strip()

        # Parse price (remove $ if present)
        try:
            price = float(price_str.replace("$", "").strip()) if price_str else None
        except ValueError:
            price = None

        # Parse product name (normalize)
        product_name = brand.strip()

        # Generate product_id (normalized product name)
        product_id = product_name.lower().replace(" ", "_").replace(".", "")

        # Parse specification
        parsed_spec = self.parser.parse(spec)

        # Validate
        validation = ValidationResult()

        # Check required fields
        valid, msg = self.validator.validate_product_name(product_name)
        if not valid:
            validation.add_error(msg)

        valid, msg = self.validator.validate_price(price)
        if not valid:
            validation.add_warning(msg)  # Warn but don't fail

        # Calculate hash_diff for SCD2 detection
        hash_diff_data = {
            "price": price,
            "stock": None,  # Not in sample data
            "screen_size": parsed_spec["screen_size"],
            "cpu_type": parsed_spec["cpu_type"],
            "builtin_ram": parsed_spec["builtin_ram"],
            "builtin_memory": parsed_spec["builtin_memory"],
            "operating_system": parsed_spec["operating_system"]
        }
        hash_diff = calculate_hash(hash_diff_data)

        # Build clean record
        clean_record = {
            "source_id": self.source_id,
            "composite_key": composite_key,
            "hash_diff": hash_diff,
            "product_id": product_id,
            "product_name": product_name,
            "category": "laptops",  # TODO: extract from source or infer
            "price": price,
            "currency": "USD",
            "stock": None,
            "description": spec,
            "screen_size": parsed_spec["screen_size"],
            "cpu_type": parsed_spec["cpu_type"],
            "builtin_ram": parsed_spec["builtin_ram"],
            "builtin_memory": parsed_spec["builtin_memory"],
            "operating_system": parsed_spec["operating_system"],
            "url": None,
            "source_hash": source_hash,
            "validation_status": validation.status,
            "validation_errors": str(validation) if validation.errors else None
        }

        return clean_record
