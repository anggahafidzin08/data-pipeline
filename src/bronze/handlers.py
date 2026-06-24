import logging
from typing import List, Dict, Any
from datetime import datetime
from src.common.connectors import get_supabase_client
from src.common.utils import calculate_hash
from src.common.config import get_settings
from src.common.exceptions import DatabaseError

logger = logging.getLogger(__name__)

class BronzeIngester:
    """Ingest raw scraped data into Bronze layer."""

    def __init__(self):
        self.db = get_supabase_client()
        settings = get_settings()
        self.source_id = settings.source_id

    def ingest(self, products: List[Dict[str, Any]]) -> int:
        """Ingest scraped products into raw_products table."""
        if not products:
            logger.warning("No products to ingest")
            return 0

        rows_to_insert = []

        for product in products:
            composite_key = product.get("composite_key")
            raw_data = product.get("raw_data")
            scraped_at = product.get("scraped_at")

            if not composite_key or not raw_data:
                logger.warning(f"Skipping invalid product: {product}")
                continue

            # Calculate hash for deduplication
            hash_raw = calculate_hash(raw_data)

            # Check if this exact record already exists
            try:
                existing = self.db.execute_query(
                    """
                    SELECT id FROM raw_products
                    WHERE source_id = %s AND composite_key = %s AND hash_raw = %s
                    LIMIT 1
                    """,
                    (self.source_id, composite_key, hash_raw)
                )

                if existing:
                    logger.debug(f"Skipping duplicate: {composite_key} (hash: {hash_raw})")
                    continue

            except DatabaseError as e:
                logger.warning(f"Failed to check for duplicates: {e}")

            rows_to_insert.append({
                "source_id": self.source_id,
                "composite_key": composite_key,
                "raw_data": raw_data,  # JSONB
                "scraped_at": scraped_at,
                "hash_raw": hash_raw
            })

        if not rows_to_insert:
            logger.info("All products were duplicates")
            return 0

        # Batch insert
        try:
            inserted_count = self.db.insert_rows("raw_products", rows_to_insert)
            logger.info(f"Inserted {inserted_count} rows into raw_products")
            return inserted_count

        except DatabaseError as e:
            logger.error(f"Failed to insert into Bronze: {e}")
            raise
