import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime
from src.common.connectors import get_supabase_client
from src.common.exceptions import DatabaseError

logger = logging.getLogger(__name__)

class SCD2Merger:
    """Merge cleaned products into Silver layer with SCD Type 2 tracking."""

    def __init__(self):
        self.db = get_supabase_client()

    def merge(self, cleaned_products: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Merge cleaned products into Silver layer.
        Returns: (inserted_count, updated_count)
        """
        inserted_count = 0
        updated_count = 0

        for product in cleaned_products:
            try:
                result = self._merge_single(product)
                if result == "inserted":
                    inserted_count += 1
                elif result == "updated":
                    updated_count += 1
            except DatabaseError as e:
                logger.error(f"Failed to merge product {product.get('product_id')}: {e}")
                continue

        logger.info(f"SCD2 merge complete: {inserted_count} inserted, {updated_count} updated")
        return inserted_count, updated_count

    def _merge_single(self, product: Dict[str, Any]) -> str:
        """
        Merge a single product using SCD Type 2.
        Returns: "inserted" or "updated" or "skipped"
        """
        composite_key = product.get("composite_key")
        hash_diff = product.get("hash_diff")

        # Find current version (is_current = true)
        try:
            existing = self.db.execute_query(
                """
                SELECT id, hash_diff FROM products_clean
                WHERE composite_key = %s AND is_current = true
                LIMIT 1
                """,
                (composite_key,)
            )
        except DatabaseError as e:
            logger.warning(f"Failed to query existing record: {e}")
            # Insert as new
            return self._insert_product(product)

        if not existing:
            # New product - insert
            return self._insert_product(product)

        # Product exists - check if changed
        existing_hash = existing[0].get("hash_diff")

        if existing_hash == hash_diff:
            # No change - skip
            logger.debug(f"No change detected for {composite_key}")
            return "skipped"

        # Data changed - end old version and insert new one
        logger.debug(f"Change detected for {composite_key}")
        return self._update_product(existing[0].get("id"), product)

    def _insert_product(self, product: Dict[str, Any]) -> str:
        """Insert new product version."""
        try:
            sql = """
            INSERT INTO products_clean (
                source_id, composite_key, hash_diff, product_id, product_name, category,
                price, currency, stock, description, screen_size, cpu_type, builtin_ram,
                builtin_memory, operating_system, url, insert_ts, is_current, source_hash,
                validation_status, validation_errors
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                CURRENT_TIMESTAMP, true, %s, %s, %s
            )
            """

            params = (
                product.get("source_id"),
                product.get("composite_key"),
                product.get("hash_diff"),
                product.get("product_id"),
                product.get("product_name"),
                product.get("category"),
                product.get("price"),
                product.get("currency"),
                product.get("stock"),
                product.get("description"),
                product.get("screen_size"),
                product.get("cpu_type"),
                product.get("builtin_ram"),
                product.get("builtin_memory"),
                product.get("operating_system"),
                product.get("url"),
                product.get("source_hash"),
                product.get("validation_status"),
                product.get("validation_errors")
            )

            self.db.execute_update(sql, params)
            logger.info(f"Inserted new version of {product.get('product_id')}")
            return "inserted"

        except DatabaseError as e:
            logger.error(f"Failed to insert product: {e}")
            raise

    def _update_product(self, existing_id: str, new_product: Dict[str, Any]) -> str:
        """End old version and insert new version."""
        try:
            # End old version
            self.db.execute_update(
                """
                UPDATE products_clean
                SET end_ts = CURRENT_TIMESTAMP, is_current = false
                WHERE id = %s
                """,
                (existing_id,)
            )

            # Insert new version
            self._insert_product(new_product)
            logger.info(f"Updated {new_product.get('product_id')} with new version")
            return "updated"

        except DatabaseError as e:
            logger.error(f"Failed to update product: {e}")
            raise
