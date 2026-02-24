# cz-revenue-telemetry — Product Specification

## Mission

Make it easy for CloudZero customers to automate sending revenue data from business systems into CloudZero's unit metric telemetry API, enabling unit economics (e.g., cost per dollar of revenue) segmented by any custom dimension.

## Target User

CloudZero customers who want to connect revenue data to cloud cost data for unit economic analysis. Typically a FinOps practitioner, cloud engineer, or RevOps person who has access to both Salesforce and CloudZero.

## Problem

Revenue data lives in business systems (Salesforce, Campfire, HubSpot, Stripe, etc.) with no automated bridge to CloudZero's telemetry API. Customers must either manually upload CSVs or go without revenue-based unit economics entirely. This creates a gap between cost visibility and business context.

## User Personas

### Primary: FinOps Practitioner
- Has CloudZero API key access
- Wants to see cost-per-customer, cost-per-product, cost-per-dollar-of-revenue
- Comfortable with CLI tools and config files
- Needs to set up once and have it run on a schedule

### Secondary: RevOps / Sales Ops
- Owns the Salesforce data
- May help configure the SOQL query and field mappings
- Less technical — needs clear documentation

## Product Behavior

### Core Flow

1. Customer creates a YAML config file defining:
   - CloudZero API key (via env var reference)
   - Telemetry stream name and granularity
   - Source type and credentials (via env var references)
   - Source query (e.g., SOQL for Salesforce)
   - Field mappings: which source fields map to `timestamp`, `value`, and `associated_cost` dimensions
2. Customer runs the CLI: `cz-revenue-telemetry sync --config config.yaml`
3. Tool connects to the source, executes the query, retrieves revenue records
4. Tool transforms each record into a CloudZero unit metric telemetry payload
5. Tool batches and sends records to `POST /unit-cost/v1/telemetry/metric/{stream_name}/replace`
6. Tool logs results: records sent, errors, API responses

### Config File Format

```yaml
cloudzero:
  api_key_env: CZ_API_KEY          # env var name containing the API key
  stream_name: revenue-by-customer  # telemetry stream name
  granularity: DAILY                # DAILY or MONTHLY

source:
  type: salesforce
  auth:
    username_env: SF_USERNAME
    password_env: SF_PASSWORD
    security_token_env: SF_SECURITY_TOKEN
    domain: login  # or custom domain for sandboxes
  query: >
    SELECT Amount, CloseDate, Account.Name, Product2.Name
    FROM OpportunityLineItem
    WHERE Opportunity.StageName = 'Closed Won'
    AND Opportunity.CloseDate >= {start_date}
    AND Opportunity.CloseDate <= {end_date}

mapping:
  timestamp_field: CloseDate
  value_field: Amount
  associated_cost:
    "custom:Customer": Account.Name
    "custom:Product": Product2.Name
```

### Operational Modes

The tool supports two modes of operation aligned with the revenue lifecycle:

**Historical Backfill (first run):**
Load past revenue data to establish a baseline for unit economics trending. Customer specifies a date range explicitly.

```bash
cz-revenue-telemetry sync --config config.yaml --start 2025-03-01 --end 2026-02-28
```

**Monthly Sync (ongoing):**
After the monthly book close (typically 5-15 business days after month-end), pull the previous month's finalized revenue. This is the default when no dates are specified.

```bash
# Run around the 15th of each month — pulls previous month's data
cz-revenue-telemetry sync --config config.yaml
```

**Re-run / Correction:**
If revenue numbers are adjusted after initial close, re-run for that specific month. Because the tool uses `/replace` (not `/sum`), this is safe and idempotent — it overwrites rather than double-counts.

```bash
cz-revenue-telemetry sync --config config.yaml --start 2026-01-01 --end 2026-01-31
```

**Date parameterization:** The SOQL query uses `{start_date}` and `{end_date}` placeholders that the tool injects based on CLI arguments or the default previous-month calculation. Customers write the query template once; the tool handles the date math.

### Edge Cases

- **Missing values**: Records with null/zero `value_field` are skipped with a warning
- **Missing dimension values**: Records with null dimension fields are skipped with a warning
- **Idempotent re-runs**: Uses CloudZero's `/replace` endpoint (not `/sum`), so re-running for the same period overwrites rather than double-counts. Safe to retry on failure or re-run after revenue adjustments.
- **Large result sets**: Salesforce SOQL has a 2,000 record default limit. Tool handles pagination via `simple-salesforce`'s built-in support.
- **API rate limits**: CloudZero allows 100 records/sec, 5MB/request. Tool batches records (up to ~5,000 per request) and respects rate limits.
- **Auth failures**: Clear error messages for both Salesforce and CloudZero auth issues.
- **Books not yet closed**: If run too early in the month, data may be incomplete. The tool logs a reminder but doesn't block — some customers may want preliminary numbers.

### CLI Interface

```
cz-revenue-telemetry sync --config config.yaml [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--dry-run] [--verbose]
cz-revenue-telemetry validate --config config.yaml
cz-revenue-telemetry version
```

- `sync` — Run the full extract-transform-load pipeline
  - No dates: defaults to previous calendar month
  - `--start` / `--end`: explicit date range (both required if either is provided)
- `validate` — Check config syntax, test connections, preview first few records without sending
- `version` — Print version
- `--dry-run` — Transform and display records but don't send to CloudZero
- `--verbose` — Detailed logging

## Success Criteria

- Customer can go from zero to sending revenue telemetry in under 30 minutes
- Config file is the only thing a customer needs to customize — no code changes
- Records appear correctly in CloudZero's unit metric analytics with the expected dimensions
- Clear error messages when something goes wrong (bad credentials, bad query, API errors)

## Milestones

### MVP (Milestone 1)
Salesforce connector with full unit metric telemetry pipeline.

- YAML config parsing and validation
- Salesforce authentication and SOQL query execution
- Record transformation (source fields → CloudZero telemetry format)
- Batched API submission to CloudZero unit metric `/replace` endpoint (idempotent)
- Date range support: explicit `--start`/`--end` or default to previous month
- CLI with `sync`, `validate`, `--dry-run`, `--verbose`
- Error handling and logging
- Documentation: README with setup guide and example configs

### V1 (Milestone 2)
Operational hardening and additional connectors.

- HubSpot connector
- Stripe connector
- Retry logic with exponential backoff for API failures
- Lambda deployment template (SAM or CDK)
- Config validation with descriptive error messages

### V2 (Milestone 3)
Extensibility and community.

- Connector plugin architecture (customers can add their own sources)
- Campfire connector
- Generic REST API connector (pull from any HTTP endpoint)
- Generic database connector (SQL query against any DB)

### Out of Scope
- Allocation telemetry streams / cost splitting
- CSV upload (CloudZero already supports this natively)
- Web UI or hosted service
- Real-time / streaming ingestion
- CloudZero dimension or CostFormation management

## Tech Stack

| Component | Choice | Rationale |
|---|---|---|
| Language | Python 3.10+ | Accessible, good Salesforce libraries, Lambda-compatible |
| CLI | Click | Clean CLI framework, better than argparse for subcommands |
| Salesforce | simple-salesforce | Mature, well-maintained, handles auth and pagination |
| HTTP | httpx | Modern async-capable HTTP client, good error handling |
| Config | PyYAML + pydantic | YAML for human editing, pydantic for validation |
| Testing | pytest | Standard, good fixture support |
| Packaging | pyproject.toml + pip | Installable via pip, also clone-and-run friendly |

## High-Level Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌─────────────┐
│   Config     │────▶│   Source     │────▶│  Transform  │────▶│  CloudZero  │
│   (YAML)     │     │  Connector   │     │   Engine    │     │   Client    │
└─────────────┘     └──────────────┘     └─────────────┘     └─────────────┘
                          │                     │                    │
                    Salesforce API        Map fields to         POST /unit-cost
                    (SOQL query)         telemetry format      /v1/telemetry/
                                                           metric/.../replace
```

### Module Structure

```
cz_revenue_telemetry/
├── __init__.py
├── cli.py              # Click CLI entry point
├── config.py           # YAML loading + pydantic models
├── sources/
│   ├── __init__.py
│   ├── base.py         # Abstract base connector
│   └── salesforce.py   # Salesforce connector
├── transform.py        # Source records → CZ telemetry records
├── cloudzero.py        # CloudZero API client
└── models.py           # Shared data models (TelemetryRecord, etc.)
```

### API Design (Internal)

**Source Connector Interface:**
```python
class BaseSource(ABC):
    def __init__(self, config: SourceConfig): ...
    def connect(self) -> None: ...
    def fetch_records(self, start_date: date, end_date: date) -> list[dict]: ...
    def test_connection(self) -> bool: ...
```

**Transform:**
```python
def transform_records(
    raw_records: list[dict],
    mapping: MappingConfig,
    granularity: str
) -> list[TelemetryRecord]: ...
```

**CloudZero Client:**
```python
class CloudZeroClient:
    def __init__(self, api_key: str): ...
    def send_telemetry(self, stream_name: str, records: list[TelemetryRecord]) -> SendResult: ...
    def test_connection(self) -> bool: ...
```

### Data Flow

1. `cli.py` loads config via `config.py`
2. Instantiates the appropriate source connector from `sources/`
3. Calls `fetch_records()` to get raw data from the source
4. Passes raw records + mapping config to `transform.py`
5. `transform.py` produces a list of `TelemetryRecord` objects
6. `cloudzero.py` batches and sends records to the API
7. CLI logs results

### CloudZero API Payload (Target)

```json
POST /unit-cost/v1/telemetry/metric/{stream_name}/replace
Authorization: <api-key>
Content-Type: application/json

{
  "records": [
    {
      "timestamp": "2026-01-15T00:00:00",
      "value": "125000.50",
      "granularity": "DAILY",
      "associated_cost": {
        "custom:Customer": "Acme Corp",
        "custom:Product": "Enterprise Plan"
      }
    }
  ]
}
```

### Batching Strategy

- Batch up to 5,000 records per API request (well under 5MB limit)
- Send batches sequentially with a small delay to stay under 100 records/sec
- Log progress: "Sending batch 1/3 (5000 records)..."
- On 503 ("slow down"): exponential backoff and retry (max 3 retries)

## Hosting / Deployment

Customer-managed. The tool is designed to be run as:
- **Cron job** on any machine with Python
- **AWS Lambda** on a schedule (CloudWatch Events / EventBridge)
- **GitHub Actions** scheduled workflow
- **Any CI/CD pipeline** on a timer

MVP does not include deployment templates — the tool is just a Python package. V1 adds a Lambda template.
