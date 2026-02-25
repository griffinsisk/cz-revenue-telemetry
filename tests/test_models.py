"""Tests for data models."""

from cz_revenue_telemetry.models import SendResult, TelemetryRecord


class TestTelemetryRecord:
    def test_to_payload_basic(self):
        record = TelemetryRecord(
            timestamp="2026-01-15",
            value="50000",
            granularity="MONTHLY",
        )
        payload = record.to_payload()
        assert payload == {
            "timestamp": "2026-01-15T00:00:00",
            "value": "50000",
            "granularity": "MONTHLY",
        }

    def test_to_payload_with_dimensions(self):
        record = TelemetryRecord(
            timestamp="2026-01-15",
            value="50000",
            granularity="DAILY",
            associated_cost={"custom:Customer": "Acme Corp", "custom:Product": "Pro"},
        )
        payload = record.to_payload()
        assert payload["associated_cost"] == {
            "custom:Customer": "Acme Corp",
            "custom:Product": "Pro",
        }

    def test_to_payload_no_dimensions_omits_key(self):
        record = TelemetryRecord(
            timestamp="2026-01-15", value="100", granularity="DAILY"
        )
        assert "associated_cost" not in record.to_payload()


class TestSendResult:
    def test_success_when_all_sent(self):
        result = SendResult(total_records=10, sent_records=10)
        assert result.success is True

    def test_failure_when_batches_fail(self):
        result = SendResult(total_records=10, sent_records=5, failed_batches=1)
        assert result.success is False

    def test_failure_when_no_records_sent(self):
        result = SendResult(total_records=0, sent_records=0)
        assert result.success is False
