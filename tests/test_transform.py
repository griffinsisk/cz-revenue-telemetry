"""Tests for the transform engine."""

from cz_revenue_telemetry.config import MappingConfig
from cz_revenue_telemetry.transform import transform_records, _get_nested_value


class TestGetNestedValue:
    def test_flat_key(self):
        assert _get_nested_value({"Amount": 100}, "Amount") == 100

    def test_dot_notation_key(self):
        record = {"Account.Name": "Acme"}
        assert _get_nested_value(record, "Account.Name") == "Acme"

    def test_nested_dict_fallback(self):
        record = {"Account": {"Name": "Acme"}}
        assert _get_nested_value(record, "Account.Name") == "Acme"

    def test_missing_key(self):
        assert _get_nested_value({"Amount": 100}, "Missing") is None

    def test_deep_nesting(self):
        record = {"Opportunity.Account.Name": "Deep"}
        assert _get_nested_value(record, "Opportunity.Account.Name") == "Deep"


class TestTransformRecords:
    def _mapping(self, **overrides):
        defaults = {
            "timestamp_field": "CloseDate",
            "value_field": "Amount",
            "associated_cost": {"custom:Customer": "Account.Name"},
        }
        defaults.update(overrides)
        return MappingConfig(**defaults)

    def test_basic_transform(self):
        records = [
            {"CloseDate": "2026-01-15", "Amount": 50000, "Account.Name": "Acme"},
            {"CloseDate": "2026-01-20", "Amount": 30000, "Account.Name": "Globex"},
        ]
        result = transform_records(records, self._mapping(), "MONTHLY")
        assert len(result) == 2
        assert result[0].timestamp == "2026-01-15"
        assert result[0].value == "50000.0"
        assert result[0].associated_cost == {"custom:Customer": "Acme"}
        assert result[0].granularity == "MONTHLY"

    def test_skips_null_value(self):
        records = [
            {"CloseDate": "2026-01-15", "Amount": None, "Account.Name": "Acme"},
        ]
        result = transform_records(records, self._mapping(), "MONTHLY")
        assert len(result) == 0

    def test_skips_zero_value(self):
        records = [
            {"CloseDate": "2026-01-15", "Amount": 0, "Account.Name": "Acme"},
        ]
        result = transform_records(records, self._mapping(), "MONTHLY")
        assert len(result) == 0

    def test_skips_negative_value(self):
        records = [
            {"CloseDate": "2026-01-15", "Amount": -100, "Account.Name": "Acme"},
        ]
        result = transform_records(records, self._mapping(), "MONTHLY")
        assert len(result) == 0

    def test_skips_missing_timestamp(self):
        records = [
            {"Amount": 50000, "Account.Name": "Acme"},
        ]
        result = transform_records(records, self._mapping(), "MONTHLY")
        assert len(result) == 0

    def test_skips_missing_dimension(self):
        records = [
            {"CloseDate": "2026-01-15", "Amount": 50000},
        ]
        result = transform_records(records, self._mapping(), "MONTHLY")
        assert len(result) == 0

    def test_truncates_timestamp_to_date(self):
        records = [
            {"CloseDate": "2026-01-15T14:30:00Z", "Amount": 100, "Account.Name": "Acme"},
        ]
        result = transform_records(records, self._mapping(), "DAILY")
        assert result[0].timestamp == "2026-01-15"

    def test_no_dimensions(self):
        mapping = self._mapping(associated_cost={})
        records = [{"CloseDate": "2026-01-15", "Amount": 100}]
        result = transform_records(records, mapping, "MONTHLY")
        assert len(result) == 1
        assert result[0].associated_cost == {}

    def test_multiple_dimensions(self):
        mapping = self._mapping(
            associated_cost={"custom:Customer": "Account.Name", "custom:Product": "Product.Name"}
        )
        records = [
            {"CloseDate": "2026-01-15", "Amount": 100, "Account.Name": "Acme", "Product.Name": "Pro"},
        ]
        result = transform_records(records, mapping, "MONTHLY")
        assert result[0].associated_cost == {"custom:Customer": "Acme", "custom:Product": "Pro"}
