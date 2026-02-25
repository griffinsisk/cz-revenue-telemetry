"""Salesforce source connector."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Dict, List

from simple_salesforce import Salesforce, SalesforceAuthenticationFailed

from cz_revenue_telemetry.config import SourceConfig
from cz_revenue_telemetry.sources.base import BaseSource

logger = logging.getLogger(__name__)


def _flatten_record(record: dict, prefix: str = "") -> Dict[str, Any]:
    """Flatten a nested Salesforce record into dot-notation keys.

    Salesforce returns nested objects like:
        {"Account": {"Name": "Acme", "attributes": {...}}, "Amount": 100}

    This flattens to:
        {"Account.Name": "Acme", "Amount": 100}
    """
    flat: Dict[str, Any] = {}
    for key, value in record.items():
        if key == "attributes":
            continue
        full_key = f"{prefix}{key}" if not prefix else f"{prefix}.{key}"
        if isinstance(value, dict) and "attributes" in value:
            # Nested Salesforce object — recurse
            flat.update(_flatten_record(value, full_key))
        elif isinstance(value, dict):
            flat.update(_flatten_record(value, full_key))
        else:
            flat[full_key] = value
    return flat


class SalesforceSource(BaseSource):
    """Connector for Salesforce via simple-salesforce."""

    def __init__(self, config: SourceConfig):
        super().__init__(config)
        self._sf: Salesforce | None = None

    def connect(self) -> None:
        """Authenticate to Salesforce."""
        auth = self.config.auth.resolve()
        try:
            self._sf = Salesforce(
                username=auth["username"],
                password=auth["password"],
                security_token=auth["security_token"],
                domain=auth["domain"],
            )
            logger.info("Connected to Salesforce as %s", auth["username"])
        except SalesforceAuthenticationFailed as e:
            raise ConnectionError(f"Salesforce authentication failed: {e}") from e

    def fetch_records(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Execute the configured SOQL query and return flattened records."""
        if self._sf is None:
            raise RuntimeError("Not connected. Call connect() first.")

        query = self.config.query.format(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        logger.info("Executing SOQL: %s", query)

        results = self._sf.query_all(query)
        raw_records = results.get("records", [])
        logger.info("Fetched %d records from Salesforce", len(raw_records))

        return [_flatten_record(r) for r in raw_records]

    def test_connection(self) -> bool:
        """Test Salesforce connectivity by querying org limits."""
        if self._sf is None:
            try:
                self.connect()
            except ConnectionError:
                return False
        try:
            self._sf.limits()  # type: ignore[union-attr]
            return True
        except Exception:
            return False
