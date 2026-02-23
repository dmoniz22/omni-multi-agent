"""Configuration loader for OMNI.

Loads configuration from YAML files and environment variables.
Uses Pydantic Settings with custom YAML source.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from omni.core.constants import (
    DEFAULT_API_HOST,
    DEFAULT_API_PORT,
    DEFAULT_GRADIO_PORT,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MAX_STEPS,
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_TIMEOUT_SECONDS,
)


class YamlConfigSource(PydanticBaseSettingsSource):
    """Custom settings source that loads from YAML files."""

    def __init__(self, settings_cls: type, yaml_files: List[Path]):
        super().__init__(settings_cls)
        self.yaml_files = yaml_files

    def get_field_value(self, field: Field, field_name: str) -> tuple[Any, str, bool]:
        """Get field value from YAML files."""
        for yaml_file in self.yaml_files:
            if yaml_file.exists():
                with open(yaml_file, "r") as f:
                    data = yaml.safe_load(f)
                    if data and field_name in data:
                        return data[field_name], field_name, False
        return None, field_name, False

    def __call__(self) -> Dict[str, Any]:
        """Load all settings from YAML files."""
        result = {}
        for yaml_file in self.yaml_files:
            if yaml_file.exists():
                with open(yaml_file, "r") as f:
                    data = yaml.safe_load(f)
                    if data:
                        result.update(data)
        return result


class LoggingSettings(BaseSettings):
    """Logging configuration."""

    model_config = SettingsConfigDict(env_prefix="LOG_", extra="ignore")

    level: str = "INFO"
    format: str = "json"
    component_levels: Dict[str, str] = Field(default_factory=dict)


class OrchestratorSettings(BaseSettings):
    """Orchestrator configuration."""

    model_config = SettingsConfigDict(extra="ignore")

    max_steps: int = DEFAULT_MAX_STEPS
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    max_retries: int = DEFAULT_MAX_RETRIES
    retry_delay_seconds: int = 1


class HITLSettings(BaseSettings):
    """Human-in-the-loop configuration."""

    model_config = SettingsConfigDict(extra="ignore")

    enabled: bool = True
    require_confirmation_for: List[str] = Field(
        default_factory=lambda: [
            "destructive_operations",
            "external_api_calls",
            "file_writes",
        ]
    )


class CircuitBreakerSettings(BaseSettings):
    """Circuit breaker configuration."""

    model_config = SettingsConfigDict(extra="ignore")

    failure_threshold: int = 3
    recovery_timeout_seconds: int = 60


class MemorySettings(BaseSettings):
    """Memory configuration."""

    model_config = SettingsConfigDict(env_prefix="MEMORY_", extra="ignore")

    embedding_model: str = "nomic-embed-text"
    vector_dimension: int = 768
    similarity_threshold: float = 0.7
    top_k: int = 5


class SessionSettings(BaseSettings):
    """Session configuration."""

    model_config = SettingsConfigDict(env_prefix="SESSION_", extra="ignore")

    timeout_minutes: int = 60
    max_concurrent: int = 10
    cleanup_interval_minutes: int = 30


class SecuritySettings(BaseSettings):
    """Security configuration."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    auth_enabled: bool = True
    jwt_secret: str = Field(default="change-me-in-production", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expiration_hours: int = 24
    cors_origins: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:7860",
            "http://localhost:3000",
        ]
    )


class APISettings(BaseSettings):
    """API configuration."""

    model_config = SettingsConfigDict(env_prefix="API_", extra="ignore")

    host: str = DEFAULT_API_HOST
    port: int = DEFAULT_API_PORT
    workers: int = 1


class DashboardSettings(BaseSettings):
    """Dashboard configuration."""

    model_config = SettingsConfigDict(env_prefix="GRADIO_", extra="ignore")

    server_name: str = "0.0.0.0"
    server_port: int = DEFAULT_GRADIO_PORT
    share: bool = False


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    url: str = Field(
        default="sqlite+aiosqlite:///omni.db",
        alias="DATABASE_URL",
    )
    pool_size: int = 10
    max_overflow: int = 20


class OllamaSettings(BaseSettings):
    """Ollama configuration."""

    model_config = SettingsConfigDict(env_prefix="OLLAMA_", extra="ignore")

    base_url: str = DEFAULT_OLLAMA_BASE_URL
    default_timeout: int = 120


class Settings(BaseSettings):
    """Main settings class combining all configuration sources.

    Priority (highest to lowest):
    1. Environment variables
    2. YAML config files
    3. Default values
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment
    env: str = Field(default="development", alias="OMNI_ENV")
    debug: bool = Field(default=True, alias="OMNI_DEBUG")
    version: str = "0.1.0"

    # Component settings
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    orchestrator: OrchestratorSettings = Field(default_factory=OrchestratorSettings)
    hitl: HITLSettings = Field(default_factory=HITLSettings)
    circuit_breaker: CircuitBreakerSettings = Field(
        default_factory=CircuitBreakerSettings
    )
    memory: MemorySettings = Field(default_factory=MemorySettings)
    session: SessionSettings = Field(default_factory=SessionSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    api: APISettings = Field(default_factory=APISettings)
    dashboard: DashboardSettings = Field(default_factory=DashboardSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customize settings sources to include YAML files."""
        config_dir = Path(__file__).parent.parent.parent.parent / "config"
        yaml_files = [
            config_dir / "settings.yaml",
            config_dir / "models.yaml",
            config_dir / "departments.yaml",
            config_dir / "skills.yaml",
        ]

        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSource(settings_cls, yaml_files),
            file_secret_settings,
        )


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance.

    Returns:
        Settings: The configured settings instance.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from disk.

    Useful when configuration files have been modified.

    Returns:
        Settings: The reloaded settings instance.
    """
    global _settings
    _settings = Settings()
    return _settings
