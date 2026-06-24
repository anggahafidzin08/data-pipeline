import pytest
from unittest.mock import Mock, patch
from src.bronze.scraper import Scraper

@pytest.fixture
def scraper():
    return Scraper(source_url="http://test.example.com")

def test_scraper_extracts_products(scraper):
    """Test that scraper extracts product data correctly."""
    html = '''
    <div class="thumbnail">
        <a class="title" title="Packard 255 G2"></a>
        <h4 class="price">$416.99</h4>
        <p class="description">15.6", AMD E2-3800 1.3GHz, 4GB, 500GB, Windows 8.1</p>
    </div>
    '''

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    products = scraper._extract_products(soup)

    assert len(products) == 1
    assert products[0]["raw_data"]["brand"] == "Packard 255 G2"
    assert products[0]["raw_data"]["price"] == "$416.99"
    assert "AMD" in products[0]["raw_data"]["spec"]

def test_scraper_generates_composite_key(scraper):
    """Test that composite_key is generated correctly."""
    html = '<div class="thumbnail"><a class="title" title="ThinkPad X240"></a><h4 class="price">$100</h4></div>'

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    products = scraper._extract_products(soup)

    assert products[0]["composite_key"] == "thinkpad_x240"
