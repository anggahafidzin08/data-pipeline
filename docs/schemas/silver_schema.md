# Silver Schema: products_clean

## Purpose
Cleaned, validated, and deduplicated product data with SCD Type 2 tracking for full audit trail.

## Table Definition

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Unique row ID |
| `source_id` | VARCHAR(255) | Source identifier (e.g., "ecommerce_site") |
| `composite_key` | VARCHAR(255) | Product identifier from source |
| `hash_diff` | VARCHAR(32) | Hash of dimension fields for SCD2 detection |
| `product_id` | VARCHAR(255) | Normalized product identifier |
| `product_name` | VARCHAR(500) | Cleaned product name |
| `category` | VARCHAR(255) | Product category |
| `price` | DECIMAL(10,2) | Current price in currency |
| `currency` | VARCHAR(10) | Currency code (e.g., "USD") |
| `stock` | INTEGER | Stock quantity (if available) |
| `description` | TEXT | Full product description |
| `screen_size` | VARCHAR(50) | Parsed screen size (e.g., "15.6\"") |
| `cpu_type` | VARCHAR(255) | Parsed CPU type (e.g., "AMD E2-3800 1.3GHz") |
| `builtin_ram` | VARCHAR(50) | Parsed RAM (e.g., "4GB") |
| `builtin_memory` | VARCHAR(50) | Parsed storage (e.g., "500GB") |
| `operating_system` | VARCHAR(100) | Parsed OS (e.g., "Windows 8.1") |
| `url` | TEXT | Product URL |
| `insert_ts` | TIMESTAMP | Insert timestamp (defaults to CURRENT_TIMESTAMP) |
| `end_ts` | TIMESTAMP | End timestamp for SCD2 (NULL if current) |
| `is_current` | BOOLEAN | Flag for current record (default: TRUE) |
| `source_hash` | VARCHAR(32) | Hash of raw data from Bronze |
| `validation_status` | VARCHAR(20) | Validation result: PASS, WARN, FAIL |
| `validation_errors` | TEXT | Validation error messages if any |

## Constraints
- Indexes on: composite_key (lookup), is_current (filtering), insert_ts (time-range queries)

## SCD Type 2 Tracking
When data changes (detected by hash_diff):
1. Current version: end_ts is set to CURRENT_TIMESTAMP, is_current = false
2. New version: inserted with is_current = true, end_ts = NULL

## Sample Data
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "source_id": "ecommerce_site",
  "composite_key": "packard_255_g2",
  "hash_diff": "a1b2c3d4e5f6g7h8",
  "product_id": "packard_255_g2",
  "product_name": "Packard 255 G2",
  "category": "laptops",
  "price": 416.99,
  "currency": "USD",
  "stock": null,
  "description": "15.6\", AMD E2-3800 1.3GHz, 4GB, 500GB, Windows 8.1",
  "screen_size": "15.6\"",
  "cpu_type": "AMD E2-3800 1.3GHz",
  "builtin_ram": "4GB",
  "builtin_memory": "500GB",
  "operating_system": "Windows 8.1",
  "url": null,
  "insert_ts": "2026-06-24T02:01:30Z",
  "end_ts": null,
  "is_current": true,
  "source_hash": "a1b2c3d4e5f6g7h8i9j0",
  "validation_status": "PASS",
  "validation_errors": null
}
```
