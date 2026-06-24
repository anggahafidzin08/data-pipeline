import pytest
from src.silver.parser import SpecParser

def test_parse_typical_laptop_spec():
    """Test parsing a typical laptop spec."""
    spec = '15.6", AMD E2-3800 1.3GHz, 4GB, 500GB, Windows 8.1'
    result = SpecParser.parse(spec)

    assert result["screen_size"] == '15.6"'
    assert "AMD E2-3800" in result["cpu_type"]
    assert result["builtin_ram"] == "4GB"
    assert result["operating_system"].lower().startswith("windows")

def test_parse_intel_laptop():
    """Test parsing Intel-based laptop."""
    spec = '12.5", Core i5-4300U, 8GB, 240GB SSD, Win7 Pro 64bit'
    result = SpecParser.parse(spec)

    assert '12.5"' in result["screen_size"]
    assert "Core i5" in result["cpu_type"]
    assert "8GB" in result["builtin_ram"]

def test_parse_missing_fields():
    """Test parsing with missing fields."""
    spec = 'AMD E2, 4GB'
    result = SpecParser.parse(spec)

    # Should default to "Unknown" for missing fields
    assert result["screen_size"] == "Unknown"
    assert result["builtin_memory"] == "Unknown"

def test_parse_empty_spec():
    """Test parsing empty spec."""
    result = SpecParser.parse(None)

    assert result["screen_size"] == "Unknown"
    assert result["operating_system"] == "Unknown"
