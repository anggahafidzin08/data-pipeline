import pytest
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file before any tests run
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

@pytest.fixture
def sample_raw_product():
    """Sample raw product data."""
    return {
        "composite_key": "packard_255_g2",
        "hash_raw": "abc123",
        "raw_data": {
            "brand": "Packard 255 G2",
            "price": "$416.99",
            "spec": '15.6", AMD E2-3800 1.3GHz, 4GB, 500GB, Windows 8.1'
        },
        "scraped_at": "2026-06-24T02:00:00Z"
    }

@pytest.fixture
def sample_clean_product():
    """Sample cleaned product data."""
    return {
        "source_id": "ecommerce_site",
        "composite_key": "packard_255_g2",
        "hash_diff": "hash_diff_123",
        "product_id": "packard_255_g2",
        "product_name": "Packard 255 G2",
        "category": "laptops",
        "price": 416.99,
        "currency": "USD",
        "stock": None,
        "description": '15.6", AMD E2-3800 1.3GHz, 4GB, 500GB, Windows 8.1',
        "screen_size": '15.6"',
        "cpu_type": "AMD E2-3800 1.3GHz",
        "builtin_ram": "4GB",
        "builtin_memory": "500GB",
        "operating_system": "Windows 8.1",
        "url": None,
        "source_hash": "abc123",
        "validation_status": "PASS",
        "validation_errors": None
    }
