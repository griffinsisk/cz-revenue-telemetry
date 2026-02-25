"""Tests for the CLI."""

from datetime import date

from click.testing import CliRunner

from cz_revenue_telemetry.cli import main, _default_date_range


class TestDefaultDateRange:
    def test_returns_previous_month(self):
        start, end = _default_date_range()
        today = date.today()
        # Start should be first of previous month
        assert start.day == 1
        # End should be last day of that same month
        assert end.month == start.month
        assert end >= start
        # Should be in the past
        assert end < today


class TestCLI:
    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_sync_missing_config(self):
        runner = CliRunner()
        result = runner.invoke(main, ["sync", "--config", "/nonexistent.yaml"])
        assert result.exit_code != 0
        assert "Config error" in result.output or "Error" in result.output

    def test_sync_start_without_end(self):
        runner = CliRunner()
        result = runner.invoke(main, ["sync", "--config", "x.yaml", "--start", "2026-01-01"])
        assert result.exit_code != 0

    def test_validate_missing_config(self):
        runner = CliRunner()
        result = runner.invoke(main, ["validate", "--config", "/nonexistent.yaml"])
        assert result.exit_code != 0

    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "sync" in result.output
        assert "validate" in result.output

    def test_sync_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["sync", "--help"])
        assert result.exit_code == 0
        assert "--config" in result.output
        assert "--start" in result.output
        assert "--end" in result.output
        assert "--dry-run" in result.output
