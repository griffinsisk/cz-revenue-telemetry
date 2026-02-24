# Architecture

## System Design

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌─────────────┐
│   Config     │────▶│   Source     │────▶│  Transform  │────▶│  CloudZero  │
│   (YAML)     │     │  Connector   │     │   Engine    │     │   Client    │
└─────────────┘     └──────────────┘     └─────────────┘     └─────────────┘
      │                    │                     │                    │
  pydantic          Salesforce API        Map fields to      POST /unit-cost/
  validation        (SOQL + pagination)   telemetry format   v1/telemetry/
                                                             metric/.../replace
```

## Components

### CLI (`cli.py`)
Entry point. Handles argument parsing (`--config`, `--start`, `--end`, `--dry-run`, `--verbose`), date defaulting (previous month if no dates), and orchestrates the pipeline.

### Config (`config.py`)
Loads YAML, validates with pydantic models, resolves env var references to actual values. Fails fast with clear errors if config is invalid or env vars are missing.

### Source Connectors (`sources/`)
Abstract `BaseSource` interface. Each connector implements `connect()`, `fetch_records(start_date, end_date)`, and `test_connection()`. Salesforce connector uses `simple-salesforce`, injects `{start_date}`/`{end_date}` into the SOQL template, handles pagination.

### Transform (`transform.py`)
Takes raw dicts from the source and a mapping config. Extracts `timestamp`, `value`, and `associated_cost` fields using dot-notation field paths (e.g., `Account.Name`). Skips records with null/zero values. Returns `TelemetryRecord` objects.

### CloudZero Client (`cloudzero.py`)
Handles batching (up to 5,000 records per request), rate limiting, and HTTP communication with the CloudZero API. Uses `/replace` endpoint for idempotency. Retries on 503 with backoff.

## Data Flow

1. CLI parses args, resolves date range
2. Config loads and validates YAML
3. Source connector authenticates and fetches records for date range
4. Transform maps raw records to `TelemetryRecord` list
5. CloudZero client batches and sends via `/replace`
6. CLI logs summary (records sent, errors, skipped)

## Key Design Decisions

- **`/replace` over `/sum`**: Revenue data is finalized monthly. Re-runs must be safe. `/replace` is idempotent.
- **Date parameterization**: SOQL uses `{start_date}`/`{end_date}` placeholders so the same config works for backfill and monthly sync.
- **Env var references**: Config stores env var *names*, not values. Secrets never touch disk.
- **Flexible dimensions**: `associated_cost` mapping is fully customer-defined. No hardcoded dimension keys.
