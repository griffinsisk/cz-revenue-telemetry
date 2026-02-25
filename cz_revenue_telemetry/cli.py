"""CLI entry point for cz-revenue-telemetry."""

from __future__ import annotations

import logging
import sys
from datetime import date, timedelta
from typing import Optional

import click

from cz_revenue_telemetry import __version__
from cz_revenue_telemetry.cloudzero import CloudZeroClient
from cz_revenue_telemetry.config import load_config
from cz_revenue_telemetry.models import SyncContext
from cz_revenue_telemetry.sources.salesforce import SalesforceSource
from cz_revenue_telemetry.transform import transform_records

logger = logging.getLogger("cz_revenue_telemetry")

SOURCE_REGISTRY = {
    "salesforce": SalesforceSource,
}


def _default_date_range() -> tuple[date, date]:
    """Return the first and last day of the previous calendar month."""
    today = date.today()
    last_day_prev_month = today.replace(day=1) - timedelta(days=1)
    first_day_prev_month = last_day_prev_month.replace(day=1)
    return first_day_prev_month, last_day_prev_month


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.setLevel(level)
    logger.addHandler(handler)


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """Send revenue data from business systems to CloudZero telemetry."""


@main.command()
@click.option("--config", "config_path", required=True, help="Path to YAML config file")
@click.option("--start", "start_date", type=click.DateTime(formats=["%Y-%m-%d"]), default=None,
              help="Start date (YYYY-MM-DD). Defaults to first day of previous month.")
@click.option("--end", "end_date", type=click.DateTime(formats=["%Y-%m-%d"]), default=None,
              help="End date (YYYY-MM-DD). Defaults to last day of previous month.")
@click.option("--dry-run", is_flag=True, help="Transform and display records without sending")
@click.option("--verbose", is_flag=True, help="Enable detailed logging")
def sync(
    config_path: str,
    start_date: Optional[click.DateTime],
    end_date: Optional[click.DateTime],
    dry_run: bool,
    verbose: bool,
) -> None:
    """Pull revenue data from source and send to CloudZero."""
    _setup_logging(verbose)

    # Validate date args
    if (start_date is None) != (end_date is None):
        raise click.UsageError("--start and --end must both be provided, or both omitted.")

    if start_date and end_date:
        s_date = start_date.date()  # type: ignore[union-attr]
        e_date = end_date.date()  # type: ignore[union-attr]
    else:
        s_date, e_date = _default_date_range()

    logger.info("Date range: %s to %s", s_date, e_date)

    # Load config
    try:
        config = load_config(config_path)
    except (FileNotFoundError, ValueError) as e:
        click.echo(f"Config error: {e}", err=True)
        sys.exit(1)

    # Connect to source
    source_cls = SOURCE_REGISTRY.get(config.source.type)
    if not source_cls:
        click.echo(f"Unknown source type: {config.source.type}", err=True)
        sys.exit(1)

    source = source_cls(config.source)
    try:
        source.connect()
    except (ConnectionError, ValueError) as e:
        click.echo(f"Source connection failed: {e}", err=True)
        sys.exit(1)

    # Fetch records
    try:
        raw_records = source.fetch_records(s_date, e_date)
    except Exception as e:
        click.echo(f"Failed to fetch records: {e}", err=True)
        sys.exit(1)

    if not raw_records:
        click.echo("No records found for the specified date range.")
        sys.exit(0)

    click.echo(f"Fetched {len(raw_records)} records from {config.source.type}")

    # Transform
    telemetry_records = transform_records(
        raw_records, config.mapping, config.cloudzero.granularity
    )

    if not telemetry_records:
        click.echo("No valid records after transformation. Check warnings above.")
        sys.exit(1)

    click.echo(f"Transformed {len(telemetry_records)} valid telemetry records")

    # Dry run — show sample and exit
    if dry_run:
        click.echo("\n--- DRY RUN (not sending) ---")
        sample = telemetry_records[:5]
        for r in sample:
            click.echo(f"  {r.to_payload()}")
        if len(telemetry_records) > 5:
            click.echo(f"  ... and {len(telemetry_records) - 5} more")
        sys.exit(0)

    # Send to CloudZero
    api_key = config.cloudzero.resolve_api_key()
    client = CloudZeroClient(api_key)
    try:
        result = client.send_telemetry(config.cloudzero.stream_name, telemetry_records)
    finally:
        client.close()

    # Report results
    click.echo(f"\nStream: {config.cloudzero.stream_name}")
    click.echo(f"Sent: {result.sent_records}/{result.total_records} records")

    if result.failed_batches:
        click.echo(f"Failed batches: {result.failed_batches}", err=True)
        for error in result.errors:
            click.echo(f"  {error}", err=True)
        sys.exit(1)

    click.echo("Done.")


@main.command()
@click.option("--config", "config_path", required=True, help="Path to YAML config file")
def validate(config_path: str) -> None:
    """Validate config and test connections."""
    _setup_logging(verbose=False)

    # Load config
    try:
        config = load_config(config_path)
        click.echo("Config: OK")
    except (FileNotFoundError, ValueError) as e:
        click.echo(f"Config: FAILED — {e}", err=True)
        sys.exit(1)

    # Test CloudZero connection
    try:
        api_key = config.cloudzero.resolve_api_key()
        cz_client = CloudZeroClient(api_key)
        if cz_client.test_connection():
            click.echo("CloudZero API: OK")
        else:
            click.echo("CloudZero API: FAILED — could not reach API", err=True)
        cz_client.close()
    except ValueError as e:
        click.echo(f"CloudZero API: FAILED — {e}", err=True)

    # Test source connection
    source_cls = SOURCE_REGISTRY.get(config.source.type)
    if source_cls:
        source = source_cls(config.source)
        try:
            if source.test_connection():
                click.echo(f"{config.source.type.title()} connection: OK")
            else:
                click.echo(f"{config.source.type.title()} connection: FAILED", err=True)
        except Exception as e:
            click.echo(f"{config.source.type.title()} connection: FAILED — {e}", err=True)
