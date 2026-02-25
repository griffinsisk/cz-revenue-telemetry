"""CloudZero telemetry API client."""

from __future__ import annotations

import logging
import time
from typing import List

import httpx

from cz_revenue_telemetry.models import SendResult, TelemetryRecord

logger = logging.getLogger(__name__)

BASE_URL = "https://api.cloudzero.com"
BATCH_SIZE = 5000
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds, doubled each retry


class CloudZeroClient:
    """Client for sending unit metric telemetry to CloudZero."""

    def __init__(self, api_key: str):
        self._client = httpx.Client(
            base_url=BASE_URL,
            headers={
                "Authorization": api_key,
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    def send_telemetry(self, stream_name: str, records: List[TelemetryRecord]) -> SendResult:
        """Send telemetry records to CloudZero in batches.

        Uses the /replace endpoint for idempotent sends.
        """
        result = SendResult(total_records=len(records))

        if not records:
            logger.warning("No records to send")
            return result

        batches = [records[i : i + BATCH_SIZE] for i in range(0, len(records), BATCH_SIZE)]
        logger.info("Sending %d records in %d batch(es)", len(records), len(batches))

        for batch_num, batch in enumerate(batches, 1):
            logger.info("Sending batch %d/%d (%d records)...", batch_num, len(batches), len(batch))
            payload = {"records": [r.to_payload() for r in batch]}

            success = self._send_with_retry(stream_name, payload)
            if success:
                result.sent_records += len(batch)
            else:
                result.failed_batches += 1
                result.errors.append(f"Batch {batch_num} failed after {MAX_RETRIES} retries")

        return result

    def _send_with_retry(self, stream_name: str, payload: dict) -> bool:
        """Send a single batch with retry on 503."""
        url = f"/unit-cost/v1/telemetry/metric/{stream_name}/replace"
        backoff = RETRY_BACKOFF

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self._client.post(url, json=payload)

                if response.status_code == 200:
                    return True

                if response.status_code == 503 and attempt < MAX_RETRIES:
                    logger.warning(
                        "Rate limited (503), retrying in %ds (attempt %d/%d)",
                        backoff, attempt, MAX_RETRIES,
                    )
                    time.sleep(backoff)
                    backoff *= 2
                    continue

                logger.error(
                    "CloudZero API error: %d %s", response.status_code, response.text
                )
                return False

            except httpx.HTTPError as e:
                if attempt < MAX_RETRIES:
                    logger.warning("HTTP error: %s, retrying in %ds", e, backoff)
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    logger.error("HTTP error after %d attempts: %s", MAX_RETRIES, e)
                    return False

        return False

    def test_connection(self) -> bool:
        """Test CloudZero API connectivity."""
        try:
            response = self._client.get("/unit-cost/v1/telemetry")
            # 200 or 403 both indicate the API is reachable;
            # 403 means bad key but the endpoint exists
            return response.status_code in (200, 403)
        except httpx.HTTPError:
            return False

    def close(self) -> None:
        self._client.close()
