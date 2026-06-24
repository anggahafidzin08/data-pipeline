#!/usr/bin/env python3
"""Initialize database tables in Supabase."""

import psycopg2
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common.config import get_settings
from src.common.exceptions import DatabaseError

def create_bronze_table(conn):
    """Create raw_products (Bronze) table."""
    sql = """
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

    CREATE INDEX idx_raw_products_composite_key ON raw_products(source_id, composite_key);
    CREATE INDEX idx_raw_products_loaded_at ON raw_products(loaded_at);
    """

    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print("✓ Created raw_products table")

def create_silver_table(conn):
    """Create products_clean (Silver) table with SCD2."""
    sql = """
    CREATE TABLE IF NOT EXISTS products_clean (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        source_id VARCHAR(255) NOT NULL,
        composite_key VARCHAR(255) NOT NULL,
        hash_diff VARCHAR(32) NOT NULL,
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

    CREATE INDEX idx_products_clean_composite_key ON products_clean(source_id, composite_key);
    CREATE INDEX idx_products_clean_is_current ON products_clean(is_current);
    CREATE INDEX idx_products_clean_insert_ts ON products_clean(insert_ts);
    """

    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print("✓ Created products_clean table")

def create_gold_tables(conn):
    """Create Gold layer tables: dim_product, dim_date, fact_products."""
    sql = """
    CREATE TABLE IF NOT EXISTS dim_date (
        dim_date_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        date_value DATE NOT NULL UNIQUE,
        year INTEGER NOT NULL,
        month INTEGER NOT NULL,
        day_of_week VARCHAR(10) NOT NULL,
        week_of_year INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS dim_product (
        dim_product_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        product_id_source VARCHAR(255) NOT NULL,
        product_name VARCHAR(500),
        description TEXT,
        screen_size VARCHAR(50),
        cpu_type VARCHAR(255),
        builtin_ram VARCHAR(50),
        builtin_memory VARCHAR(50),
        operating_system VARCHAR(100),
        url TEXT,
        effective_from DATE NOT NULL,
        effective_to DATE,
        is_current BOOLEAN DEFAULT TRUE,
        scd2_version INTEGER DEFAULT 1,
        UNIQUE(product_id_source, scd2_version)
    );

    CREATE TABLE IF NOT EXISTS fact_products (
        fact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        dim_product_id UUID NOT NULL REFERENCES dim_product(dim_product_id),
        dim_date_id UUID NOT NULL REFERENCES dim_date(dim_date_id),
        price_amount DECIMAL(10,2),
        stock_quantity INTEGER,
        loaded_date DATE DEFAULT CURRENT_DATE,
        source_id VARCHAR(255),
        UNIQUE(dim_product_id, dim_date_id)
    );

    CREATE INDEX idx_dim_product_is_current ON dim_product(is_current);
    CREATE INDEX idx_fact_products_date ON fact_products(loaded_date);
    """

    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print("✓ Created Gold tables (dim_date, dim_product, fact_products)")

def main():
    settings = get_settings()

    try:
        # Note: This is a placeholder. In production, would need proper Supabase
        # connection setup with correct authentication.
        print("Database initialization skipped (requires proper Supabase setup)")
        print("Tables to create:")
        print("  - raw_products (Bronze)")
        print("  - products_clean (Silver)")
        print("  - dim_date, dim_product, fact_products (Gold)")

    except DatabaseError as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
