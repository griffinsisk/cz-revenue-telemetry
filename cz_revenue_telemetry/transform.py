"""Transform source records into CloudZero telemetry records."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from cz_revenue_telemetry.config import MappingConfig
from cz_revenue_telemetry.models import TelemetryRecord

logger = logging.getLogger(__name__)


def _get_nested_value(record: Dict[str, Any], field_path: str) -> Any:
    """Get a value from a flat dict using a dot-notation key.

    The record is already flattened by the source connector, so we first
    try a direct key match. If not found, we walk the dot path for nested dicts.
    """
    if field_path in record:
        return record[field_path]

    parts = field_path.split(".")
    current = record
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def transform_records(
    raw_records: List[Dict[str, Any]],
    mapping: MappingConfig,
    granularity: str,
) -> List[TelemetryRecord]:
    """Transform raw source records into CloudZero telemetry records.

    Returns a list of valid TelemetryRecord objects. Records with missing
    or invalid values are skipped with warnings.
    """
    telemetry_records: List[TelemetryRecord] = []
    skipped = 0

    for i, record in enumerate(raw_records):
        # Extract timestamp
        timestamp = _get_nested_value(record, mapping.timestamp_field)
        if not timestamp:
            logger.warning("Record %d: missing timestamp field '%s', skipping", i, mapping.timestamp_field)
            skipped += 1
            continue

        # Normalize timestamp to date string (YYYY-MM-DD)
        ts_str = str(timestamp)[:10]

        # Extract value
        raw_value = _get_nested_value(record, mapping.value_field)
        if raw_value is None:
            logger.warning("Record %d: missing value field '%s', skipping", i, mapping.value_field)
            skipped += 1
            continue

        try:
            numeric_value = float(raw_value)
        except (ValueError, TypeError):
            logger.warning("Record %d: non-numeric value '%s', skipping", i, raw_value)
            skipped += 1
            continue

        if numeric_value <= 0:
            logger.warning("Record %d: value must be > 0 (got %s), skipping", i, numeric_value)
            skipped += 1
            continue

        # Extract associated_cost dimensions
        associated_cost: Dict[str, str] = {}
        skip_record = False
        for dimension_key, source_field in mapping.associated_cost.items():
            dim_value = _get_nested_value(record, source_field)
            if dim_value is None:
                logger.warning(
                    "Record %d: missing dimension value for '%s' (field '%s'), skipping",
                    i, dimension_key, source_field,
                )
                skip_record = True
                break
            associated_cost[dimension_key] = str(dim_value)

        if skip_record:
            skipped += 1
            continue

        telemetry_records.append(
            TelemetryRecord(
                timestamp=ts_str,
                value=str(numeric_value),
                granularity=granularity,
                associated_cost=associated_cost,
            )
        )

    if skipped:
        logger.warning("Skipped %d of %d records due to missing/invalid data", skipped, len(raw_records))

    logger.info("Transformed %d records into telemetry format", len(telemetry_records))
    return telemetry_records
