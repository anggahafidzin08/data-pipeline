import logging
import sys
from datetime import datetime
from src.common.logging import setup_logging
from src.common.config import get_settings
from src.common.connectors import get_supabase_client
from src.bronze.scraper import Scraper
from src.bronze.handlers import BronzeIngester
from src.silver.transformer import Transformer
from src.silver.scd2_merge import SCD2Merger
from src.common.exceptions import PipelineError

logger = logging.getLogger(__name__)


class Pipeline:
    """Main data pipeline orchestrator."""

    def __init__(self):
        setup_logging()
        self.settings = get_settings()
        self.start_time = datetime.utcnow()
        self.stats = {
            "bronze_inserted": 0,
            "silver_inserted": 0,
            "silver_updated": 0,
            "errors": []
        }
        self.db = get_supabase_client()

    def _init_db(self):
        """Create tables if they don't exist."""
        try:
            # Bronze layer
            self.db.execute_update("""
                CREATE TABLE IF NOT EXISTS raw_products (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    source_id VARCHAR(255) NOT NULL,
                    composite_key VARCHAR(255) NOT NULL,
                    raw_data JSONB NOT NULL,
                    scraped_at TIMESTAMP NOT NULL,
                    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    hash_raw VARCHAR(32) NOT NULL,
                    UNIQUE(source_id, composite_key, hash_raw)
                );
                CREATE INDEX IF NOT EXISTS idx_raw_products_composite_key
                    ON raw_products(source_id, composite_key);
                CREATE INDEX IF NOT EXISTS idx_raw_products_loaded_at
                    ON raw_products(loaded_at);
            """)

            # Silver layer
            self.db.execute_update("""
                CREATE TABLE IF NOT EXISTS products_clean (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    source_id VARCHAR(255),
                    composite_key VARCHAR(255),
                    hash_diff VARCHAR(32),
                    product_id VARCHAR(255),
                    product_name VARCHAR(500),
                    category VARCHAR(255),
                    price DECIMAL(10,2),
                    currency VARCHAR(10),
                    stock INTEGER,
                    description TEXT,
                    screen_size VARCHAR(50),
                    cpu_type VARCHAR(255),
                    builtin_ram VARCHAR(50),
                    builtin_memory VARCHAR(50),
                    operating_system VARCHAR(100),
                    url TEXT,
                    insert_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_ts TIMESTAMP,
                    is_current BOOLEAN DEFAULT TRUE,
                    source_hash VARCHAR(32),
                    validation_status VARCHAR(20),
                    validation_errors TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_products_clean_composite_key
                    ON products_clean(source_id, composite_key);
                CREATE INDEX IF NOT EXISTS idx_products_clean_is_current
                    ON products_clean(is_current);
                CREATE INDEX IF NOT EXISTS idx_products_clean_insert_ts
                    ON products_clean(insert_ts);
            """)
            logger.info("Database tables initialized")
        except Exception as e:
            logger.warning(f"Table initialization skipped (may already exist or no DB): {e}")

    def run(self):
        """Execute full pipeline: Bronze → Silver → Gold."""
        try:
            logger.info(f"Starting pipeline run at {self.start_time}")

            # Initialize tables if needed
            self._init_db()

            # Phase 1: Bronze
            logger.info("=== BRONZE LAYER ===")
            self._run_bronze()

            # Phase 2: Silver
            logger.info("=== SILVER LAYER ===")
            self._run_silver()

            # Phase 3: Gold (TBD - simplified for MVP)
            logger.info("=== GOLD LAYER ===")
            logger.info("Gold layer loading skipped for MVP")

            # Report
            logger.info("=== PIPELINE COMPLETE ===")
            self._report_stats()

        except PipelineError as e:
            logger.error(f"Pipeline failed: {e}")
            sys.exit(1)

    def _run_bronze(self):
        """Run Bronze layer: scrape and ingest."""
        try:
            scraper = Scraper()
            raw_products = scraper.scrape()
            logger.info(f"Scraped {len(raw_products)} products")

            ingester = BronzeIngester()
            inserted = ingester.ingest(raw_products)
            self.stats["bronze_inserted"] = inserted

        except Exception as e:
            logger.error(f"Bronze layer failed: {e}")
            raise PipelineError(f"Bronze layer failed: {e}")

    def _run_silver(self):
        """Run Silver layer: transform and merge."""
        try:
            # Read from Bronze
            db = get_supabase_client()

            # Get new records from Bronze since last run (TBD: track last run time)
            raw_records = db.execute_query(
                """
                SELECT id, composite_key, raw_data, hash_raw
                FROM raw_products
                ORDER BY loaded_at DESC
                LIMIT 1000
                """
            )
            logger.info(f"Reading {len(raw_records)} records from Bronze")

            # Transform
            transformer = Transformer()
            cleaned_products = transformer.transform(raw_records)

            # Merge (SCD2)
            merger = SCD2Merger()
            inserted, updated = merger.merge(cleaned_products)
            self.stats["silver_inserted"] = inserted
            self.stats["silver_updated"] = updated

        except Exception as e:
            logger.error(f"Silver layer failed: {e}")
            raise PipelineError(f"Silver layer failed: {e}")

    def _report_stats(self):
        """Report pipeline statistics."""
        duration = (datetime.utcnow() - self.start_time).total_seconds()
        logger.info(f"Duration: {duration:.2f}s")
        logger.info(f"Bronze inserted: {self.stats['bronze_inserted']}")
        logger.info(f"Silver inserted: {self.stats['silver_inserted']}")
        logger.info(f"Silver updated: {self.stats['silver_updated']}")


if __name__ == "__main__":
    pipeline = Pipeline()
    pipeline.run()
