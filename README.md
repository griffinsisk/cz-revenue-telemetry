# cz-revenue-telemetry

Automate sending revenue data from Salesforce (and other business systems) to [CloudZero](https://www.cloudzero.com) as unit metric telemetry. Enables unit economics like cost-per-customer, cost-per-product, or cost-per-dollar-of-revenue — segmented by any custom dimension you define.

## How It Works

1. You write a YAML config that defines your revenue source, query, and dimension mappings
2. The tool pulls revenue records from your source (Salesforce)
3. Transforms them into CloudZero unit metric telemetry records
4. Sends them to the CloudZero API via the `/replace` endpoint (idempotent — safe to re-run)

## Quick Start

### 1. Install

```bash
pip install git+https://github.com/griffinsisk/cz-revenue-telemetry.git
```

Or clone and install locally:

```bash
git clone https://github.com/griffinsisk/cz-revenue-telemetry.git
cd cz-revenue-telemetry
pip install .
```

### 2. Set Environment Variables

```bash
export CZ_API_KEY=your-cloudzero-api-key
export SF_USERNAME=your-salesforce-username
export SF_PASSWORD=your-salesforce-password
export SF_SECURITY_TOKEN=your-salesforce-security-token
```

Your CloudZero API key needs the `unit-cost_v1:manage_telemetry_records` scope. Generate one at **Settings > API Keys** in the CloudZero UI.

Your Salesforce security token can be reset from **Personal Settings > Reset My Security Token** in Salesforce.

### 3. Create a Config File

```yaml
cloudzero:
  api_key_env: CZ_API_KEY
  stream_name: revenue-by-customer
  granularity: MONTHLY

source:
  type: salesforce
  auth:
    username_env: SF_USERNAME
    password_env: SF_PASSWORD
    security_token_env: SF_SECURITY_TOKEN
    domain: login
  query: >
    SELECT Amount, CloseDate, Account.Name
    FROM Opportunity
    WHERE StageName = 'Closed Won'
    AND CloseDate >= {start_date}
    AND CloseDate <= {end_date}

mapping:
  timestamp_field: CloseDate
  value_field: Amount
  associated_cost:
    "custom:Customer": Account.Name
```

See [`examples/`](examples/) for more config examples including multi-dimension setups.

### 4. Validate Your Config

```bash
cz-revenue-telemetry validate --config config.yaml
```

This checks your config syntax and tests connections to both Salesforce and CloudZero.

### 5. Run a Dry Run

```bash
cz-revenue-telemetry sync --config config.yaml --dry-run
```

This pulls data from Salesforce and shows you what would be sent without actually sending anything.

### 6. Send Data

```bash
# Send previous month's revenue (default)
cz-revenue-telemetry sync --config config.yaml

# Send a specific date range (e.g., historical backfill)
cz-revenue-telemetry sync --config config.yaml --start 2025-01-01 --end 2025-12-31
```

## Usage

```
cz-revenue-telemetry sync --config CONFIG [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--dry-run] [--verbose]
cz-revenue-telemetry validate --config CONFIG
cz-revenue-telemetry --version
```

| Option | Description |
|---|---|
| `--config` | Path to your YAML config file (required) |
| `--start` | Start date for the query range. Defaults to first day of previous month. |
| `--end` | End date for the query range. Defaults to last day of previous month. |
| `--dry-run` | Pull and transform data but don't send to CloudZero |
| `--verbose` | Enable detailed logging |

## Config Reference

### `cloudzero`

| Field | Required | Description |
|---|---|---|
| `api_key_env` | Yes | Name of the env var containing your CloudZero API key |
| `stream_name` | Yes | Telemetry stream name (alphanumeric, hyphens, underscores, periods; max 256 chars) |
| `granularity` | No | `DAILY` or `MONTHLY` (default: `MONTHLY`) |

### `source`

| Field | Required | Description |
|---|---|---|
| `type` | Yes | Source type (`salesforce`) |
| `auth.username_env` | Yes | Env var for Salesforce username |
| `auth.password_env` | Yes | Env var for Salesforce password |
| `auth.security_token_env` | Yes | Env var for Salesforce security token |
| `auth.domain` | No | `login` (default) for production, or your custom domain for sandboxes |
| `query` | Yes | SOQL query with `{start_date}` and `{end_date}` placeholders |

### `mapping`

| Field | Required | Description |
|---|---|---|
| `timestamp_field` | Yes | Source field for the record date |
| `value_field` | Yes | Source field for the revenue amount |
| `associated_cost` | No | Map of CloudZero dimension keys to source fields (max 5) |

Dimension keys should use the `custom:` prefix for custom dimensions (e.g., `custom:Customer`, `custom:Product`).

## Operational Model

**Historical backfill:** On first use, specify `--start` and `--end` to load past revenue data.

**Monthly sync:** Run with no date arguments after your monthly book close (typically 5-15 business days after month-end). Defaults to the previous calendar month.

**Corrections:** Re-run for any date range after revenue adjustments. The tool uses CloudZero's `/replace` endpoint, so re-runs overwrite rather than double-count.

**Scheduling:** Run on a cron job, AWS Lambda with EventBridge, or GitHub Actions schedule. Example cron (runs on the 15th of each month):

```
0 8 15 * * cz-revenue-telemetry sync --config /path/to/config.yaml
```

## Writing SOQL Queries

The `query` field accepts any valid SOQL query. Use `{start_date}` and `{end_date}` as placeholders — the tool replaces them with the appropriate date range at runtime.

**Revenue by customer (Opportunities):**
```sql
SELECT Amount, CloseDate, Account.Name
FROM Opportunity
WHERE StageName = 'Closed Won'
AND CloseDate >= {start_date}
AND CloseDate <= {end_date}
```

**Revenue by customer and product (Opportunity Line Items):**
```sql
SELECT TotalPrice, Opportunity.CloseDate, Opportunity.Account.Name, Product2.Name
FROM OpportunityLineItem
WHERE Opportunity.StageName = 'Closed Won'
AND Opportunity.CloseDate >= {start_date}
AND Opportunity.CloseDate <= {end_date}
```

**Custom objects:** Use whatever Salesforce object and fields contain your revenue data. The tool doesn't assume any specific schema — just point it at the right fields.

## Limitations

- CloudZero allows a maximum of **5 `associated_cost` dimensions** per stream
- CloudZero API rate limit: **100 records/sec**, **5MB per request** (the tool handles batching automatically)
- Salesforce SOQL query results are paginated automatically
- Revenue values must be greater than 0 (zero/negative values are skipped)
- Records missing required fields (timestamp, value, or any configured dimension) are skipped with a warning

## Development

```bash
git clone https://github.com/griffinsisk/cz-revenue-telemetry.git
cd cz-revenue-telemetry
pip install -e ".[dev]"
pytest
```
