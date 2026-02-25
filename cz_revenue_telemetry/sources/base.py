"""Abstract base class for source connectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Dict, List

from cz_revenue_telemetry.config import SourceConfig


class BaseSource(ABC):
    """Abstract base for all revenue data source connectors."""

    def __init__(self, config: SourceConfig):
        self.config = config

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the source system."""

    @abstractmethod
    def fetch_records(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Fetch revenue records for the given date range.

        Returns a list of flat dicts with keys matching the source field names
        used in the mapping config (e.g., "Account.Name", "Amount").
        """

    @abstractmethod
    def test_connection(self) -> bool:
        """Test that the connection credentials are valid."""
