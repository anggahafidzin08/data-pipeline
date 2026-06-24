# E-Commerce Data Pipeline

Production-grade data pipeline with medallion architecture (Bronze → Silver → Gold).

## Quick Start

1. **Setup environment:**
   ```bash
   make setup
   cp .env.example .env
   # Edit .env with Supabase credentials
   ```

2. **Run tests:**
   ```bash
   make test
   ```

3. **Run pipeline:**
   ```bash
   python -m src.pipeline
   ```

## Architecture

See [architecture.md](./architecture.md)

## Database Schemas

- [Bronze Schema](./schemas/bronze_schema.md)
- [Silver Schema](./schemas/silver_schema.md)
- [Gold Schema](./schemas/gold_schema.md)
