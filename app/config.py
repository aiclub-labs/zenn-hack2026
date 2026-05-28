import json
import logging
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment_small: str = "gpt-5.4-mini"
    azure_openai_deployment_large: str = "gpt-5.4"
    azure_openai_api_version: str = "2025-04-01-preview"

    azure_storage_account: str = ""
    azure_storage_container: str = "artifacts"

    cosmos_endpoint: str = ""
    cosmos_database: str = "dialogue_delta"
    key_vault_uri: str = ""

    applicationinsights_connection_string: str = ""

    azure_tenant_id: str = ""
    azure_client_id: str = ""

    log_level: str = "INFO"
    environment: str = Field(default="local")

    # M-11: Entra group object ID -> list of tenant pks (sector#unit).
    # Supplied as JSON via env REVIEWER_GROUP_TENANT_MAP, e.g.:
    #   {"00000000-0000-0000-0000-000000000001": ["finance#tokyo"]}
    reviewer_group_tenant_map: dict[str, list[str]] = Field(default_factory=dict)

    # M-12: SLA cron tenant enumeration (JSON list of pks). When empty the
    # cron falls back to a cross-partition scan.
    sla_cron_tenant_pks: list[str] = Field(default_factory=list)

    @field_validator("reviewer_group_tenant_map", mode="before")
    @classmethod
    def _parse_group_map(cls, v: Any) -> Any:
        if isinstance(v, str):
            if not v.strip():
                return {}
            try:
                return json.loads(v)
            except json.JSONDecodeError as exc:
                logger.warning(
                    "REVIEWER_GROUP_TENANT_MAP invalid JSON, ignoring: %s", exc
                )
                return {}
        return v

    @field_validator("sla_cron_tenant_pks", mode="before")
    @classmethod
    def _parse_cron_pks(cls, v: Any) -> Any:
        if isinstance(v, str):
            if not v.strip():
                return []
            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, list) else []
            except json.JSONDecodeError:
                # Fallback: comma-separated.
                return [p.strip() for p in v.split(",") if p.strip()]
        return v


settings = Settings()
