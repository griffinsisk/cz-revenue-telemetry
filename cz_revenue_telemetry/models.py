"""Shared data models for cz-revenue-telemetry."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional


@dataclass
class TelemetryRecord:
    """A single CloudZero unit metric telemetry record."""

    timestamp: str  # ISO 8601 date string (YYYY-MM-DD)
    value: str  # Numeric string, must be > 0
    granularity: str  # DAILY or MONTHLY
    associated_cost: Dict[str, str] = field(default_factory=dict)

    def to_payload(self) -> dict:
        """Convert to CloudZero API payload format."""
        payload: dict = {
            "timestamp": f"{self.timestamp}T00:00:00",
            "value": self.value,
            "granularity": self.granularity,
        }
        if self.associated_cost:
            payload["associated_cost"] = self.associated_cost
        return payload


@dataclass
class SendResult:
    """Result of sending telemetry records to CloudZero."""

    total_records: int = 0
    sent_records: int = 0
    skipped_records: int = 0
    failed_batches: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.failed_batches == 0 and self.sent_records > 0


@dataclass
class SyncContext:
    """Context for a sync operation."""

    start_date: date
    end_date: date
    dry_run: bool = False
    verbose: bool = False
