# Gold Schema: Dimensional Model

## Purpose
Analytics-ready dimensional model with slowly-changing dimensions (SCD2) and fact tables.

## Tables

### dim_date - Date Dimension

| Column | Type | Description |
|--------|------|-------------|
| `dim_date_id` | UUID (PK) | Unique date dimension key |
| `date_value` | DATE | Calendar date (UNIQUE) |
| `year` | INTEGER | Year |
| `month` | INTEGER | Month (1-12) |
| `day_of_week` | VARCHAR(10) | Day name (Monday, etc.) |
| `week_of_year` | INTEGER | ISO week number |

### dim_product - Product Dimension (SCD2)

| Column | Type | Description |
|--------|------|-------------|
| `dim_product_id` | UUID (PK) | Unique product dimension key |
| `product_id_source` | VARCHAR(255) | Source product ID |
| `product_name` | VARCHAR(500) | Product name |
| `description` | TEXT | Product description |
| `screen_size` | VARCHAR(50) | Screen size |
| `cpu_type` | VARCHAR(255) | CPU type |
| `builtin_ram` | VARCHAR(50) | Built-in RAM |
| `builtin_memory` | VARCHAR(50) | Built-in storage |
| `operating_system` | VARCHAR(100) | Operating system |
| `url` | TEXT | Product URL |
| `effective_from` | DATE | Start of validity period (SCD2) |
| `effective_to` | DATE | End of validity period (SCD2, NULL if current) |
| `is_current` | BOOLEAN | Current flag (default: TRUE) |
| `scd2_version` | INTEGER | Version number (1, 2, 3...) |

Constraints: UNIQUE(product_id_source, scd2_version)

### fact_products - Product Facts (SCD1)

| Column | Type | Description |
|--------|------|-------------|
| `fact_id` | UUID (PK) | Unique fact key |
| `dim_product_id` | UUID (FK) | References dim_product |
| `dim_date_id` | UUID (FK) | References dim_date |
| `price_amount` | DECIMAL(10,2) | Price on this date |
| `stock_quantity` | INTEGER | Stock quantity on this date |
| `loaded_date` | DATE | Date of load (default: CURRENT_DATE) |
| `source_id` | VARCHAR(255) | Source identifier |

Constraints: 
- UNIQUE(dim_product_id, dim_date_id) - one fact per product per day
- Foreign keys to dim_product and dim_date

## Sample Data

### dim_date
```json
{
  "dim_date_id": "660e8400-e29b-41d4-a716-446655440010",
  "date_value": "2026-06-24",
  "year": 2026,
  "month": 6,
  "day_of_week": "Wednesday",
  "week_of_year": 26
}
```

### dim_product
```json
{
  "dim_product_id": "770e8400-e29b-41d4-a716-446655440020",
  "product_id_source": "packard_255_g2",
  "product_name": "Packard 255 G2",
  "description": "15.6\" laptop",
  "screen_size": "15.6\"",
  "cpu_type": "AMD E2-3800 1.3GHz",
  "builtin_ram": "4GB",
  "builtin_memory": "500GB",
  "operating_system": "Windows 8.1",
  "url": null,
  "effective_from": "2026-06-24",
  "effective_to": null,
  "is_current": true,
  "scd2_version": 1
}
```

### fact_products
```json
{
  "fact_id": "880e8400-e29b-41d4-a716-446655440030",
  "dim_product_id": "770e8400-e29b-41d4-a716-446655440020",
  "dim_date_id": "660e8400-e29b-41d4-a716-446655440010",
  "price_amount": 416.99,
  "stock_quantity": null,
  "loaded_date": "2026-06-24",
  "source_id": "ecommerce_site"
}
```
