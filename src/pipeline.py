import logging
import sys
import json
import os
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

CHECKPOINT_DIR = ".checkpoints"


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
        self._ensure_checkpoint_dir()

    def _ensure_checkpoint_dir(self):
        """Ensure checkpoint directory exists."""
        if not os.path.exists(CHECKPOINT_DIR):
            os.makedirs(CHECKPOINT_DIR)

    def _get_checkpoint(self, layer: str) -> tuple[str, str]:
        """
        Read last checkpoint timestamp for a layer.
        Returns (timestamp, timestamp_column) tuple.
        Checkpoints are stored by table name in a single .checkpoints/checkpoints.json file.
        """
        checkpoint_file = os.path.join(CHECKPOINT_DIR, "checkpoints.json")

        # Get source table and column name from config
        config = self.settings.checkpoint_config.get(layer, {})
        table_name = config.get("source_table", "raw_products")
        column_name = config.get("timestamp_column", "loaded_at")

        if os.path.exists(checkpoint_file):
            try:
                with open(checkpoint_file, 'r') as f:
                    checkpoints = json.load(f)
                    timestamp = checkpoints.get(table_name, "1970-01-01T00:00:00Z")
                    logger.info(f"Checkpoint for table '{table_name}': {timestamp}")
                    return timestamp, column_name
            except Exception as e:
                logger.warning(f"Failed to read checkpoint file: {e}")
                return "1970-01-01T00:00:00Z", column_name

        logger.info(f"No checkpoint file yet, starting from epoch for table '{table_name}'")
        return "1970-01-01T00:00:00Z", column_name

    def _save_checkpoint(self, layer: str, timestamp):
        """
        Save checkpoint timestamp for a layer in the central checkpoints.json file.
        Checkpoints are keyed by table name for flexibility.
        """
        checkpoint_file = os.path.join(CHECKPOINT_DIR, "checkpoints.json")
        try:
            # Convert datetime to ISO format string if needed
            if isinstance(timestamp, datetime):
                timestamp_str = timestamp.isoformat() + "Z"
            else:
                timestamp_str = str(timestamp)

            # Get table name from config
            table_name = (
                self.settings.checkpoint_config.get(layer, {}).get("source_table", "raw_products")
            )

            # Read existing checkpoints
            checkpoints = {}
            if os.path.exists(checkpoint_file):
                try:
                    with open(checkpoint_file, 'r') as f:
                        checkpoints = json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to read existing checkpoints: {e}")

            # Update this table's checkpoint
            checkpoints[table_name] = timestamp_str

            # Write back
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoints, f, indent=2)

            logger.info(f"Saved checkpoint for table '{table_name}': {timestamp_str}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint for {layer}: {e}")

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
        """Execute full pipeline: Bronze → Silver → Gold for all configured tables."""
        try:
            logger.info(f"Starting pipeline run at {self.start_time}")
            logger.info(f"Configured tables: {list(self.settings.tables.keys())}")

            # Initialize tables if needed
            self._init_db()

            # Process each configured table through all layers
            for table_name, table_config in self.settings.tables.items():
                if not table_config.get("enabled", True):
                    logger.info(f"Skipping disabled table: {table_name}")
                    continue

                logger.info(f"\n{'='*60}")
                logger.info(f"Processing table: {table_name}")
                logger.info(f"{'='*60}")

                try:
                    # Phase 1: Bronze
                    if "bronze" in table_config:
                        logger.info(f"[{table_name}] BRONZE LAYER")
                        self._run_bronze(table_name, table_config["bronze"])

                    # Phase 2: Silver
                    if "silver" in table_config:
                        logger.info(f"[{table_name}] SILVER LAYER")
                        self._run_silver(table_name, table_config["silver"])

                    # Phase 3: Gold
                    if "gold" in table_config:
                        logger.info(f"[{table_name}] GOLD LAYER")
                        logger.info(f"[{table_name}] Gold layer loading skipped for MVP")

                except Exception as e:
                    logger.error(f"Failed to process table {table_name}: {e}")
                    self.stats["errors"].append(f"{table_name}: {str(e)}")

            # Report
            logger.info(f"\n{'='*60}")
            logger.info("PIPELINE COMPLETE")
            logger.info(f"{'='*60}")
            self._report_stats()

        except PipelineError as e:
            logger.error(f"Pipeline failed: {e}")
            sys.exit(1)

    def _run_bronze(self, table_name: str, bronze_config: dict):
        """Run Bronze layer: scrape and ingest for a specific table."""
        try:
            scraper = Scraper()
            raw_products = scraper.scrape()
            logger.info(f"[{table_name}] Scraped {len(raw_products)} records")

            ingester = BronzeIngester()
            inserted = ingester.ingest(raw_products)
            self.stats["bronze_inserted"] += inserted
            logger.info(f"[{table_name}] Inserted {inserted} records into {bronze_config.get('target_table')}")

        except Exception as e:
            logger.error(f"[{table_name}] Bronze layer failed: {e}")
            raise PipelineError(f"Bronze layer failed for {table_name}: {e}")

    def _run_silver(self, table_name: str, silver_config: dict):
        """Run Silver layer: transform and merge with delta loading for a specific table."""
        try:
            db = get_supabase_client()

            source_table = silver_config.get("source_table", "raw_products")
            target_table = silver_config.get("target_table", "products_clean")
            timestamp_col = silver_config.get("source_timestamp_column", "loaded_at")

            logger.info(f"[{table_name}] Reading from {source_table} → {target_table}")

            # Get checkpoint for this target ← source combination
            # Structure: {target_table: {source_table: timestamp}}
            checkpoint_file = os.path.join(CHECKPOINT_DIR, "checkpoints.json")
            checkpoint_ts = "1970-01-01T00:00:00Z"

            if os.path.exists(checkpoint_file):
                try:
                    with open(checkpoint_file, 'r') as f:
                        checkpoints = json.load(f)
                        # Get checkpoint for this specific target_table → source_table pair
                        checkpoint_ts = (
                            checkpoints.get(target_table, {})
                            .get(source_table, "1970-01-01T00:00:00Z")
                        )
                except Exception as e:
                    logger.warning(f"[{table_name}] Failed to read checkpoint: {e}")

            logger.info(f"[{table_name}] Delta load {source_table} → {target_table} since {checkpoint_ts}")

            # Delta load: only get records newer than checkpoint
            query = f"""
                SELECT id, composite_key, raw_data, hash_raw, {timestamp_col}
                FROM {source_table}
                WHERE {timestamp_col} > %s
                ORDER BY {timestamp_col} ASC
                LIMIT 1000
            """
            raw_records = db.execute_query(query, (checkpoint_ts,))
            logger.info(f"[{table_name}] Read {len(raw_records)} new records from {source_table}")

            if not raw_records:
                logger.info(f"[{table_name}] No new records to process")
                return

            # Transform
            transformer = Transformer()
            cleaned_products = transformer.transform(raw_records)
            logger.info(f"[{table_name}] Transformed {len(cleaned_products)} records")

            # Merge (SCD2) - only if enabled in config
            if silver_config.get("scd2", {}).get("enabled", False):
                merger = SCD2Merger()
                inserted, updated = merger.merge(cleaned_products)
                self.stats["silver_inserted"] += inserted
                self.stats["silver_updated"] += updated
                logger.info(f"[{table_name}] SCD2 merge: {inserted} inserted, {updated} updated into {target_table}")
            else:
                logger.info(f"[{table_name}] SCD2 merge disabled, skipping")

            # Save checkpoint: update for this target_table ← source_table pair
            if raw_records:
                latest_timestamp = raw_records[-1].get(timestamp_col)
                if latest_timestamp:
                    # Convert datetime to ISO string if needed
                    if isinstance(latest_timestamp, datetime):
                        latest_timestamp_str = latest_timestamp.isoformat() + "Z"
                    else:
                        latest_timestamp_str = str(latest_timestamp)

                    # Update checkpoint file with nested structure
                    checkpoint_file = os.path.join(CHECKPOINT_DIR, "checkpoints.json")
                    checkpoints = {}
                    if os.path.exists(checkpoint_file):
                        try:
                            with open(checkpoint_file, 'r') as f:
                                checkpoints = json.load(f)
                        except Exception as e:
                            logger.warning(f"[{table_name}] Failed to read existing checkpoints: {e}")

                    # Ensure target_table key exists
                    if target_table not in checkpoints:
                        checkpoints[target_table] = {}

                    # Update the source_table checkpoint under this target_table
                    checkpoints[target_table][source_table] = latest_timestamp_str

                    # Write back
                    with open(checkpoint_file, 'w') as f:
                        json.dump(checkpoints, f, indent=2)
                    logger.info(f"[{table_name}] Checkpoint saved: {target_table} ← {source_table} = {latest_timestamp_str}")

        except Exception as e:
            logger.error(f"[{table_name}] Silver layer failed: {e}")
            raise PipelineError(f"Silver layer failed for {table_name}: {e}")

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
