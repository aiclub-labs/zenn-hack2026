from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment_small: str = "gpt-4o-mini"
    azure_openai_deployment_large: str = "gpt-4o"
    azure_openai_api_version: str = "2024-08-01-preview"

    azure_storage_account: str = ""
    azure_storage_container: str = "artifacts"

    applicationinsights_connection_string: str = ""

    azure_tenant_id: str = ""
    azure_client_id: str = ""

    log_level: str = "INFO"
    environment: str = Field(default="local")


settings = Settings()
