"""Tests for the Salesforce source connector."""

from datetime import date

import pytest

from cz_revenue_telemetry.config import SourceConfig
from cz_revenue_telemetry.sources.salesforce import SalesforceSource, _flatten_record


class TestFlattenRecord:
    def test_flat_record(self):
        record = {"Amount": 100, "CloseDate": "2026-01-15", "attributes": {"type": "Opportunity"}}
        flat = _flatten_record(record)
        assert flat == {"Amount": 100, "CloseDate": "2026-01-15"}

    def test_nested_record(self):
        record = {
            "Amount": 100,
            "Account": {"Name": "Acme", "attributes": {"type": "Account"}},
            "attributes": {"type": "Opportunity"},
        }
        flat = _flatten_record(record)
        assert flat == {"Amount": 100, "Account.Name": "Acme"}

    def test_deep_nesting(self):
        record = {
            "Opportunity": {
                "Account": {"Name": "Acme", "attributes": {"type": "Account"}},
                "attributes": {"type": "Opportunity"},
            },
            "TotalPrice": 500,
            "attributes": {"type": "OpportunityLineItem"},
        }
        flat = _flatten_record(record)
        assert flat == {"Opportunity.Account.Name": "Acme", "TotalPrice": 500}

    def test_empty_record(self):
        assert _flatten_record({"attributes": {"type": "Opportunity"}}) == {}

    def test_null_values_preserved(self):
        record = {"Amount": None, "attributes": {"type": "Opportunity"}}
        flat = _flatten_record(record)
        assert flat == {"Amount": None}


class TestSalesforceSource:
    def _source_config(self) -> SourceConfig:
        return SourceConfig(
            type="salesforce",
            auth={
                "username_env": "SF_USER",
                "password_env": "SF_PASS",
                "security_token_env": "SF_TOKEN",
            },
            query="SELECT Amount FROM Opportunity WHERE CloseDate >= {start_date} AND CloseDate <= {end_date}",
        )

    def test_fetch_without_connect_raises(self):
        source = SalesforceSource(self._source_config())
        with pytest.raises(RuntimeError, match="Not connected"):
            source.fetch_records(date(2026, 1, 1), date(2026, 1, 31))

    def test_connect_with_missing_env_var(self):
        source = SalesforceSource(self._source_config())
        with pytest.raises(ValueError, match="not set"):
            source.connect()

    def test_fetch_records_with_mock(self, monkeypatch):
        """Test fetch with a mocked Salesforce client."""
        monkeypatch.setenv("SF_USER", "user@test.com")
        monkeypatch.setenv("SF_PASS", "password")
        monkeypatch.setenv("SF_TOKEN", "token123")

        config = self._source_config()
        source = SalesforceSource(config)

        # Mock the Salesforce client
        class MockSF:
            def query_all(self, query):
                assert "{start_date}" not in query  # placeholders should be resolved
                return {
                    "records": [
                        {
                            "Amount": 50000,
                            "attributes": {"type": "Opportunity"},
                        },
                        {
                            "Amount": 30000,
                            "attributes": {"type": "Opportunity"},
                        },
                    ]
                }

        source._sf = MockSF()
        records = source.fetch_records(date(2026, 1, 1), date(2026, 1, 31))
        assert len(records) == 2
        assert records[0] == {"Amount": 50000}
        assert records[1] == {"Amount": 30000}
