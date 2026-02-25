"""Tests for the CloudZero API client."""

import pytest
import httpx

from cz_revenue_telemetry.cloudzero import CloudZeroClient, BATCH_SIZE
from cz_revenue_telemetry.models import TelemetryRecord


def _make_records(n: int) -> list:
    return [
        TelemetryRecord(
            timestamp=f"2026-01-{(i % 28) + 1:02d}",
            value=str(1000 + i),
            granularity="MONTHLY",
            associated_cost={"custom:Customer": f"Customer-{i}"},
        )
        for i in range(n)
    ]


class TestCloudZeroClient:
    def test_send_empty_records(self):
        client = CloudZeroClient(api_key="test-key")
        result = client.send_telemetry("test-stream", [])
        assert result.total_records == 0
        assert result.sent_records == 0
        client.close()

    def test_send_success(self, httpx_mock):
        """Test successful send with mocked HTTP."""
        httpx_mock.add_response(
            url="https://api.cloudzero.com/unit-cost/v1/telemetry/metric/test-stream/replace",
            method="POST",
            status_code=200,
            json={"status": "ok"},
        )
        client = CloudZeroClient(api_key="test-key")
        records = _make_records(3)
        result = client.send_telemetry("test-stream", records)
        assert result.sent_records == 3
        assert result.failed_batches == 0
        assert result.success is True
        client.close()

    def test_send_api_error(self, httpx_mock):
        """Test handling of API errors."""
        httpx_mock.add_response(
            url="https://api.cloudzero.com/unit-cost/v1/telemetry/metric/test-stream/replace",
            method="POST",
            status_code=400,
            json={"error": "bad request"},
        )
        client = CloudZeroClient(api_key="test-key")
        records = _make_records(2)
        result = client.send_telemetry("test-stream", records)
        assert result.sent_records == 0
        assert result.failed_batches == 1
        client.close()

    def test_batching(self, httpx_mock):
        """Test that large record sets are batched."""
        httpx_mock.add_response(
            url="https://api.cloudzero.com/unit-cost/v1/telemetry/metric/test-stream/replace",
            method="POST",
            status_code=200,
            json={"status": "ok"},
        )
        client = CloudZeroClient(api_key="test-key")
        records = _make_records(BATCH_SIZE + 100)
        result = client.send_telemetry("test-stream", records)
        assert result.sent_records == BATCH_SIZE + 100
        # Should have made 2 HTTP calls
        assert len(httpx_mock.get_requests()) == 2
        client.close()

    def test_auth_header(self, httpx_mock):
        """Test that the API key is sent correctly."""
        httpx_mock.add_response(
            url="https://api.cloudzero.com/unit-cost/v1/telemetry/metric/s/replace",
            method="POST",
            status_code=200,
        )
        client = CloudZeroClient(api_key="my-secret-key")
        client.send_telemetry("s", _make_records(1))
        request = httpx_mock.get_requests()[0]
        assert request.headers["authorization"] == "my-secret-key"
        client.close()


@pytest.fixture
def httpx_mock(monkeypatch):
    """Simple httpx mock fixture."""
    return HttpxMock(monkeypatch)


class HttpxMock:
    """Lightweight mock for httpx.Client."""

    def __init__(self, monkeypatch):
        self._responses = []
        self._requests = []
        self._monkeypatch = monkeypatch
        self._patch()

    def add_response(self, url: str, method: str = "POST", status_code: int = 200, json: dict = None):
        self._responses.append({
            "url": url,
            "method": method.upper(),
            "status_code": status_code,
            "json": json or {},
        })

    def get_requests(self):
        return self._requests

    def _patch(self):
        mock_self = self

        class MockResponse:
            def __init__(self, status_code, json_data):
                self.status_code = status_code
                self._json = json_data
                self.text = str(json_data)

            def json(self):
                return self._json

        original_init = httpx.Client.__init__

        def mock_init(client_self, *args, **kwargs):
            original_init(client_self, *args, **kwargs)

        def mock_post(client_self, url, **kwargs):
            mock_self._requests.append(type("Req", (), {
                "url": str(client_self._base_url) + url if not url.startswith("http") else url,
                "method": "POST",
                "headers": client_self.headers,
                "json": kwargs.get("json"),
            })())
            for resp in mock_self._responses:
                return MockResponse(resp["status_code"], resp["json"])
            return MockResponse(500, {"error": "no mock"})

        def mock_get(client_self, url, **kwargs):
            mock_self._requests.append(type("Req", (), {
                "url": url, "method": "GET", "headers": client_self.headers,
            })())
            for resp in mock_self._responses:
                if resp["method"] == "GET":
                    return MockResponse(resp["status_code"], resp["json"])
            return MockResponse(200, {})

        self._monkeypatch.setattr(httpx.Client, "post", mock_post)
        self._monkeypatch.setattr(httpx.Client, "get", mock_get)
