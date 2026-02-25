"""Tests for config loading and validation."""

import os
import pytest
import yaml

from cz_revenue_telemetry.config import AppConfig, CloudZeroConfig, MappingConfig, load_config


VALID_CONFIG = {
    "cloudzero": {
        "api_key_env": "CZ_API_KEY",
        "stream_name": "revenue-by-customer",
        "granularity": "MONTHLY",
    },
    "source": {
        "type": "salesforce",
        "auth": {
            "username_env": "SF_USERNAME",
            "password_env": "SF_PASSWORD",
            "security_token_env": "SF_SECURITY_TOKEN",
        },
        "query": "SELECT Amount FROM Opportunity WHERE CloseDate >= {start_date}",
    },
    "mapping": {
        "timestamp_field": "CloseDate",
        "value_field": "Amount",
        "associated_cost": {"custom:Customer": "Account.Name"},
    },
}


class TestCloudZeroConfig:
    def test_valid_stream_name(self):
        cfg = CloudZeroConfig(api_key_env="KEY", stream_name="revenue-by-customer")
        assert cfg.stream_name == "revenue-by-customer"

    def test_invalid_stream_name(self):
        with pytest.raises(ValueError, match="Invalid stream name"):
            CloudZeroConfig(api_key_env="KEY", stream_name="bad name with spaces!")

    def test_resolve_api_key(self, monkeypatch):
        monkeypatch.setenv("MY_KEY", "secret123")
        cfg = CloudZeroConfig(api_key_env="MY_KEY", stream_name="test")
        assert cfg.resolve_api_key() == "secret123"

    def test_resolve_api_key_missing(self):
        cfg = CloudZeroConfig(api_key_env="NONEXISTENT_KEY", stream_name="test")
        with pytest.raises(ValueError, match="not set"):
            cfg.resolve_api_key()

    def test_default_granularity(self):
        cfg = CloudZeroConfig(api_key_env="KEY", stream_name="test")
        assert cfg.granularity == "MONTHLY"


class TestMappingConfig:
    def test_too_many_dimensions(self):
        dims = {f"custom:dim{i}": f"field{i}" for i in range(6)}
        with pytest.raises(ValueError, match="Too many"):
            MappingConfig(timestamp_field="ts", value_field="val", associated_cost=dims)

    def test_five_dimensions_ok(self):
        dims = {f"custom:dim{i}": f"field{i}" for i in range(5)}
        cfg = MappingConfig(timestamp_field="ts", value_field="val", associated_cost=dims)
        assert len(cfg.associated_cost) == 5


class TestLoadConfig:
    def test_load_valid(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(VALID_CONFIG))
        cfg = load_config(str(config_file))
        assert cfg.cloudzero.stream_name == "revenue-by-customer"
        assert cfg.source.type == "salesforce"
        assert cfg.mapping.value_field == "Amount"

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path.yaml")

    def test_invalid_source_type(self, tmp_path):
        bad_config = {**VALID_CONFIG, "source": {**VALID_CONFIG["source"], "type": "oracle"}}
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(bad_config))
        with pytest.raises(ValueError):
            load_config(str(config_file))
