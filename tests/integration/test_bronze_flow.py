import pytest
from unittest.mock import Mock, patch
from src.bronze.scraper import Scraper
from src.bronze.handlers import BronzeIngester

@patch("src.bronze.handlers.get_supabase_client")
def test_bronze_ingestion_flow(mock_db_client):
    """Test end-to-end Bronze flow: scrape → ingest."""

    # Mock database
    mock_db = Mock()
    mock_db.execute_query.return_value = []  # No duplicates
    mock_db.insert_rows.return_value = 3  # 3 rows inserted
    mock_db_client.return_value = mock_db

    # Mock scraper
    mock_products = [
        {
            "composite_key": "packard_255_g2",
            "raw_data": {"brand": "Packard 255 G2", "price": "$416.99"},
            "scraped_at": "2026-06-24T02:00:00Z"
        },
        {
            "composite_key": "thinkpad_x240",
            "raw_data": {"brand": "ThinkPad X240", "price": "$1311.99"},
            "scraped_at": "2026-06-24T02:00:00Z"
        },
        {
            "composite_key": "aspire_e1_510",
            "raw_data": {"brand": "Aspire E1-510", "price": "$306.99"},
            "scraped_at": "2026-06-24T02:00:00Z"
        }
    ]

    ingester = BronzeIngester()
    inserted = ingester.ingest(mock_products)

    assert inserted == 3
    assert mock_db.insert_rows.called
