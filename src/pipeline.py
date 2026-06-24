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

    def run(self):
        """Execute full pipeline: Bronze → Silver → Gold."""
        try:
            logger.info(f"Starting pipeline run at {self.start_time}")

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
