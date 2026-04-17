"""Configuration loaded from environment variables."""

from dataclasses import dataclass, field
import os


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = field(default_factory=lambda: _as_bool(os.getenv("DEBUG"), False))

    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "Production AI Agent"))
    app_version: str = field(default_factory=lambda: os.getenv("APP_VERSION", "1.0.0"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())

    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    agent_api_key: str = field(default_factory=lambda: os.getenv("AGENT_API_KEY", "dev-key-change-me"))
    allowed_origins: list[str] = field(
        default_factory=lambda: [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")]
    )

    rate_limit_per_minute: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
    )
    monthly_budget_usd: float = field(
        default_factory=lambda: float(os.getenv("MONTHLY_BUDGET_USD", "10.0"))
    )
    conversation_ttl_seconds: int = field(
        default_factory=lambda: int(os.getenv("CONVERSATION_TTL_SECONDS", "86400"))
    )
    history_max_messages: int = field(
        default_factory=lambda: int(os.getenv("HISTORY_MAX_MESSAGES", "20"))
    )
    shutdown_grace_seconds: int = field(
        default_factory=lambda: int(os.getenv("SHUTDOWN_GRACE_SECONDS", "10"))
    )

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    def validate(self) -> "Settings":
        if self.is_production and self.agent_api_key == "dev-key-change-me":
            raise ValueError("AGENT_API_KEY must be changed in production")
        return self


settings = Settings().validate()
