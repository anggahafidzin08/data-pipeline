import pytest
from src.silver.transformer import Transformer

@pytest.fixture
def transformer():
    return Transformer()

def test_transform_single_product(transformer):
    """Test transforming a single product."""
    raw_product = {
        "composite_key": "packard_255_g2",
        "hash_raw": "abc123",
        "raw_data": {
            "brand": "Packard 255 G2",
            "price": "$416.99",
            "spec": '15.6", AMD E2-3800 1.3GHz, 4GB, 500GB, Windows 8.1'
        }
    }

    clean = transformer._transform_single(raw_product)

    assert clean["product_name"] == "Packard 255 G2"
    assert clean["price"] == 416.99
    assert clean["currency"] == "USD"
    assert clean["screen_size"] == '15.6"'
    assert "AMD" in clean["cpu_type"]
    assert clean["validation_status"] in ["PASS", "WARN"]

def test_transform_normalizes_product_id(transformer):
    """Test that product_id is normalized."""
    raw_product = {
        "composite_key": "thinkpad_x240",
        "hash_raw": "def456",
        "raw_data": {
            "brand": "ThinkPad X240",
            "price": "$1311.99",
            "spec": '12.5", Core i5-4300U, 8GB, 240GB SSD, Win7 Pro 64bit'
        }
    }

    clean = transformer._transform_single(raw_product)

    assert clean["product_id"] == "thinkpad_x240"

def test_transform_multiple_products(transformer):
    """Test transforming multiple products."""
    raw_products = [
        {
            "composite_key": "packard_255_g2",
            "hash_raw": "abc123",
            "raw_data": {
                "brand": "Packard 255 G2",
                "price": "$416.99",
                "spec": '15.6", AMD E2-3800 1.3GHz, 4GB, 500GB, Windows 8.1'
            }
        },
        {
            "composite_key": "thinkpad_x240",
            "hash_raw": "def456",
            "raw_data": {
                "brand": "ThinkPad X240",
                "price": "$1311.99",
                "spec": '12.5", Core i5-4300U, 8GB, 240GB SSD, Win7 Pro 64bit'
            }
        }
    ]

    cleaned = transformer.transform(raw_products)

    assert len(cleaned) == 2
    assert cleaned[0]["product_name"] == "Packard 255 G2"
    assert cleaned[1]["product_name"] == "ThinkPad X240"
