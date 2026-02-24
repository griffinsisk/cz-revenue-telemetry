# cz-revenue-telemetry

## Project Goal

Python CLI tool that automates sending revenue data from business systems (Salesforce first) to CloudZero's unit metric telemetry API. Customers configure a YAML file, run `cz-revenue-telemetry sync`, and revenue data flows into CloudZero with customer-defined dimensions for unit economics analysis.

## Architecture

```
Config (YAML) → Source Connector → Transform Engine → CloudZero Client
```

- **Source connectors** pull raw revenue records from business systems
- **Transform** maps source fields to CloudZero telemetry format
- **CloudZero client** batches and sends to `/unit-cost/v1/telemetry/metric/{stream}/replace`
- Uses `/replace` (not `/sum`) for idempotent re-runs

## Folder Structure

```
cz_revenue_telemetry/       # Source code
  cli.py                    # Click CLI entry point
  config.py                 # YAML loading + pydantic validation
  models.py                 # Shared data models
  transform.py              # Source records → CZ telemetry records
  cloudzero.py              # CloudZero API client
  sources/
    base.py                 # Abstract base connector
    salesforce.py           # Salesforce connector
tests/                      # All test files
docs/                       # Spec, architecture, changelog
examples/                   # Example config files
_CZ_Docs_/                  # CloudZero reference docs (gitignored)
```

## Commands

```bash
# Install in dev mode
pip install -e ".[dev]"

# Run the CLI
cz-revenue-telemetry sync --config config.yaml
cz-revenue-telemetry sync --config config.yaml --start 2025-01-01 --end 2025-12-31
cz-revenue-telemetry validate --config config.yaml
cz-revenue-telemetry --help

# Testing
pytest
pytest --cov=cz_revenue_telemetry
pytest tests/test_transform.py -v

# Linting & type checking
ruff check .
ruff format .
mypy cz_revenue_telemetry/
```

## Constraints

- Never hardcode credentials — always reference env var names in config
- Never commit `.env` files
- CloudZero API limits: 100 records/sec, 5MB/request, max 5 `associated_cost` dimensions per stream
- All dimension keys/values are customer-defined — no hardcoded assumptions
- Files under 500 lines
- Stream names: alphanumeric, underscores, periods, hyphens only (max 256 chars)

## Branching

- `main` — stable, releasable
- Feature branches: `feature/<name>`
- Bug fixes: `fix/<name>`
- PR before merging to main

## Key Docs

- `docs/spec.md` — Full product specification
- `docs/architecture.md` — System design and data flow
- `docs/changelog.md` — Change history
- `examples/` — Example config files for customers

Update files in the docs folder after major milestones and feature additions.
