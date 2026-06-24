# Bronze Schema: raw_products

## Purpose
Immutable append-only store of scraped data, exactly as received from source.

## Table Definition

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Unique row ID |
| `source_id` | VARCHAR(255) | Source identifier (e.g., "ecommerce_site") |
| `composite_key` | VARCHAR(255) | Unique product identifier from source |
| `raw_data` | JSONB | Complete scraped record as-is |
| `scraped_at` | TIMESTAMP | When scraper ran |
| `loaded_at` | TIMESTAMP | When inserted (defaults to CURRENT_TIMESTAMP) |
| `hash_raw` | VARCHAR(32) | MD5 of raw_data (for dedup) |

## Constraints
- UNIQUE(source_id, composite_key, hash_raw) - prevents duplicate identical records
- Indexes: composite_key lookup, loaded_at for time-range queries

## Sample Data
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "source_id": "ecommerce_site",
  "composite_key": "packard_255_g2",
  "raw_data": {
    "brand": "Packard 255 G2",
    "price": "$416.99",
    "spec": "15.6\", AMD E2-3800 1.3GHz, 4GB, 500GB, Windows 8.1"
  },
  "scraped_at": "2026-06-24T02:00:00Z",
  "loaded_at": "2026-06-24T02:01:30Z",
  "hash_raw": "a1b2c3d4e5f6g7h8"
}
```
