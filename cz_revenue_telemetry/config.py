"""YAML config loading and validation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import yaml
from pydantic import BaseModel, field_validator, model_validator


class CloudZeroConfig(BaseModel):
    """CloudZero API configuration."""

    api_key_env: str
    stream_name: str
    granularity: Literal["DAILY", "MONTHLY"] = "MONTHLY"

    @field_validator("stream_name")
    @classmethod
    def validate_stream_name(cls, v: str) -> str:
        import re

        if not re.match(r"^[\w.\-]{1,256}$", v):
            raise ValueError(
                f"Invalid stream name '{v}'. Must be 1-256 chars: "
                "alphanumeric, underscores, periods, hyphens only."
            )
        return v

    def resolve_api_key(self) -> str:
        """Resolve the API key from the environment variable."""
        value = os.environ.get(self.api_key_env)
        if not value:
            raise ValueError(
                f"Environment variable '{self.api_key_env}' is not set. "
                "Set it with your CloudZero API key."
            )
        return value


class SalesforceAuthConfig(BaseModel):
    """Salesforce authentication configuration."""

    username_env: str
    password_env: str
    security_token_env: str
    domain: str = "login"

    def resolve(self) -> Dict[str, str]:
        """Resolve all env vars to actual values."""
        resolved = {}
        for field_name, env_var in [
            ("username", self.username_env),
            ("password", self.password_env),
            ("security_token", self.security_token_env),
        ]:
            value = os.environ.get(env_var)
            if not value:
                raise ValueError(
                    f"Environment variable '{env_var}' is not set. "
                    f"Set it with your Salesforce {field_name}."
                )
            resolved[field_name] = value
        resolved["domain"] = self.domain
        return resolved


class SourceConfig(BaseModel):
    """Source system configuration."""

    type: str
    auth: SalesforceAuthConfig  # Will become a union type when more connectors are added
    query: str

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        supported = ["salesforce"]
        if v not in supported:
            raise ValueError(f"Unsupported source type '{v}'. Supported: {supported}")
        return v


class MappingConfig(BaseModel):
    """Field mapping configuration."""

    timestamp_field: str
    value_field: str
    associated_cost: Dict[str, str] = {}

    @field_validator("associated_cost")
    @classmethod
    def validate_dimension_count(cls, v: Dict[str, str]) -> Dict[str, str]:
        if len(v) > 5:
            raise ValueError(
                f"Too many associated_cost dimensions ({len(v)}). "
                "CloudZero allows a maximum of 5 per stream."
            )
        return v


class AppConfig(BaseModel):
    """Top-level application configuration."""

    cloudzero: CloudZeroConfig
    source: SourceConfig
    mapping: MappingConfig


def load_config(path: str) -> AppConfig:
    """Load and validate config from a YAML file."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(config_path) as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise ValueError(f"Config file must be a YAML mapping, got {type(raw).__name__}")

    return AppConfig(**raw)
