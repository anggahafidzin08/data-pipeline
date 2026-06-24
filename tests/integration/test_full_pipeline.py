import pytest
from unittest.mock import Mock, patch


def test_full_pipeline_flow():
    """Test end-to-end pipeline flow with mocked all layers."""
    with patch("src.common.connectors.SupabaseClient._connect") as mock_connect, \
         patch("src.bronze.scraper.Scraper.scrape") as mock_scrape, \
         patch("src.bronze.handlers.BronzeIngester.ingest") as mock_ingest, \
         patch("src.silver.transformer.Transformer.transform") as mock_transform, \
         patch("src.silver.scd2_merge.SCD2Merger.merge") as mock_merge, \
         patch("src.pipeline.get_supabase_client") as mock_db_client:

        # Mock scraper return
        mock_scrape.return_value = [
            {
                "composite_key": "packard_255_g2",
                "raw_data": {"brand": "Packard 255 G2", "price": "$416.99"},
                "scraped_at": "2026-06-24T02:00:00Z"
            }
        ]

        # Mock Bronze ingester return
        mock_ingest.return_value = 1

        # Mock transformer return
        mock_transform.return_value = [
            {
                "product_id": "packard_255_g2",
                "product_name": "Packard 255 G2",
                "price": 416.99,
                "composite_key": "packard_255_g2",
                "hash_diff": "hash123",
                "source_id": "ecommerce_site",
                "category": "laptops",
                "currency": "USD",
                "stock": None,
                "description": "test",
                "screen_size": "15.6\"",
                "cpu_type": "AMD",
                "builtin_ram": "4GB",
                "builtin_memory": "500GB",
                "operating_system": "Windows",
                "url": None,
                "source_hash": "raw_hash",
                "validation_status": "PASS",
                "validation_errors": None
            }
        ]

        # Mock SCD2 merger return
        mock_merge.return_value = (1, 0)

        # Mock database client
        mock_db = Mock()
        mock_db.execute_query.return_value = [
            {
                "id": "uuid1",
                "composite_key": "packard_255_g2",
                "raw_data": {"brand": "Packard 255 G2", "price": "$416.99"},
                "hash_raw": "raw_hash"
            }
        ]
        mock_db_client.return_value = mock_db

        # Run pipeline
        from src.pipeline import Pipeline
        pipeline = Pipeline()
        pipeline._run_bronze()
        pipeline._run_silver()

        # Verify stats
        assert pipeline.stats["bronze_inserted"] == 1
        assert pipeline.stats["silver_inserted"] == 1
        assert pipeline.stats["silver_updated"] == 0

        # Verify methods were called in correct order
        assert mock_scrape.called
        assert mock_ingest.called
        assert mock_transform.called
        assert mock_merge.called


def test_pipeline_handles_bronze_error():
    """Test pipeline gracefully handles Bronze layer errors."""
    from src.common.exceptions import PipelineError
    from src.pipeline import Pipeline

    with patch("src.bronze.scraper.Scraper.scrape") as mock_scrape:
        # Mock scraper to raise exception
        mock_scrape.side_effect = Exception("Scraping failed")

        pipeline = Pipeline()

        # Should raise PipelineError
        with pytest.raises(PipelineError):
            pipeline._run_bronze()


def test_pipeline_handles_silver_error():
    """Test pipeline gracefully handles Silver layer errors."""
    from src.common.exceptions import PipelineError
    from src.pipeline import Pipeline

    with patch("src.pipeline.get_supabase_client") as mock_db_client:
        # Mock database to raise exception
        mock_db = Mock()
        mock_db.execute_query.side_effect = Exception("Database query failed")
        mock_db_client.return_value = mock_db

        pipeline = Pipeline()

        # Should raise PipelineError
        with pytest.raises(PipelineError):
            pipeline._run_silver()
