# Stage 1 Architecture

## Layers

### Bronze (Raw)
- Append-only table: `raw_products`
- Stores scraped data exactly as received
- Deduplication by (source_id, composite_key, hash_raw)

### Silver (Cleaned)
- Table: `products_clean`
- SCD Type 2 tracking (full audit trail)
- Parsed specifications: screen_size, cpu_type, builtin_ram, builtin_memory, operating_system
- Validation: required fields, price range, data types

### Gold (Analytics)
- Dimension: `dim_product` (SCD2, product attributes)
- Dimension: `dim_date` (calendar table)
- Fact: `fact_products` (SCD1, current state)

## Data Flow

```
Scraper
  ↓
Bronze (ingest)
  ↓
Bronze Quality Checks
  ↓
Silver (transform)
  ↓
Silver Quality Checks
  ↓
Gold (load)
  ↓
Gold Quality Checks
  ↓
Pipeline Complete
```

## Technologies

- Python 3.11+
- Supabase (PostgreSQL 15)
- BeautifulSoup4 (web scraping)
- Pandas (data manipulation)
- Pydantic (validation)
- pytest (testing)
