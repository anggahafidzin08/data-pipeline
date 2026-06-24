import pytest
from unittest.mock import Mock, patch
from src.silver.scd2_merge import SCD2Merger

@patch("src.silver.scd2_merge.get_supabase_client")
def test_scd2_merge_new_product(mock_db_client):
    """Test merging a new product."""
    mock_db = Mock()
    mock_db.execute_query.return_value = []  # No existing record
    mock_db.execute_update.return_value = 1  # 1 row inserted
    mock_db_client.return_value = mock_db

    merger = SCD2Merger()
    product = {
        "composite_key": "packard_255_g2",
        "hash_diff": "hash123",
        "product_id": "packard_255_g2",
        "product_name": "Packard 255 G2",
        "price": 416.99,
        "currency": "USD",
        "source_id": "ecommerce_site",
        "category": "laptops",
        "stock": None,
        "description": "15.6\", AMD E2-3800 1.3GHz, 4GB, 500GB, Windows 8.1",
        "screen_size": "15.6\"",
        "cpu_type": "AMD E2-3800 1.3GHz",
        "builtin_ram": "4GB",
        "builtin_memory": "500GB",
        "operating_system": "Windows 8.1",
        "url": None,
        "source_hash": "raw_hash123",
        "validation_status": "PASS",
        "validation_errors": None
    }

    result = merger._merge_single(product)

    assert result == "inserted"
    assert mock_db.execute_update.called

@patch("src.silver.scd2_merge.get_supabase_client")
def test_scd2_merge_no_change(mock_db_client):
    """Test merging when data hasn't changed."""
    mock_db = Mock()
    mock_db.execute_query.return_value = [{"id": "uuid123", "hash_diff": "hash123"}]
    mock_db_client.return_value = mock_db

    merger = SCD2Merger()
    product = {
        "composite_key": "packard_255_g2",
        "hash_diff": "hash123",  # Same hash
        "product_id": "packard_255_g2",
        "product_name": "Packard 255 G2",
        "source_id": "ecommerce_site"
    }

    result = merger._merge_single(product)

    assert result == "skipped"
    # No UPDATE should be called
    assert not mock_db.execute_update.called

@patch("src.silver.scd2_merge.get_supabase_client")
def test_scd2_merge_data_changed(mock_db_client):
    """Test merging when data has changed."""
    mock_db = Mock()
    mock_db.execute_query.return_value = [{"id": "uuid123", "hash_diff": "old_hash"}]
    mock_db.execute_update.return_value = 1
    mock_db_client.return_value = mock_db

    merger = SCD2Merger()
    product = {
        "composite_key": "packard_255_g2",
        "hash_diff": "new_hash",  # Different hash
        "product_id": "packard_255_g2",
        "product_name": "Packard 255 G2",
        "price": 399.99,  # Price changed
        "source_id": "ecommerce_site",
        "currency": "USD",
        "category": "laptops",
        "stock": None,
        "description": "updated",
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

    result = merger._merge_single(product)

    assert result == "updated"
    # Both UPDATE and INSERT should be called
    assert mock_db.execute_update.call_count >= 1
