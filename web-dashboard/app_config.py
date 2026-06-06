from __future__ import annotations

import os
from functools import cached_property

from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError, field_validator


class AppSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    database_url: SecretStr = Field(min_length=12)
    database_pool_min: int = Field(default=1, ge=1, le=50)
    database_pool_max: int = Field(default=10, ge=1, le=100)
    jwt_secret: SecretStr = Field(min_length=32)
    jwt_ttl_seconds: int = Field(default=1_209_600, ge=300, le=31_536_000)
    cookie_secure: bool = False
    allowed_origins: tuple[str, ...] = (
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:8080",
        "http://localhost:8080",
    )
    rate_limit_auth_per_minute: int = Field(default=12, ge=1, le=300)
    rate_limit_api_per_minute: int = Field(default=120, ge=1, le=3000)
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = Field(default=8787, ge=1, le=65535)
    app_environment: str = "development"
    require_alembic_migrations: bool = False
    stripe_secret_key: SecretStr | None = None
    stripe_webhook_secret: SecretStr | None = None
    stripe_success_url: str = "http://127.0.0.1:5173/?checkout=success"
    stripe_cancel_url: str = "http://127.0.0.1:5173/?checkout=cancelled"
    stripe_price_starter: str | None = None
    stripe_price_pro: str | None = None
    stripe_price_enterprise: str | None = None

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value()
        if not raw.startswith(("postgresql://", "postgres://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return value

    @field_validator("database_pool_max")
    @classmethod
    def validate_pool_bounds(cls, value: int, info) -> int:
        min_value = info.data.get("database_pool_min", 1)
        if value < min_value:
            raise ValueError("DATABASE_POOL_MAX must be greater than or equal to DATABASE_POOL_MIN")
        return value

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value) -> tuple[str, ...]:
        if isinstance(value, str):
            parts = [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]
        else:
            parts = [str(origin).strip().rstrip("/") for origin in value if str(origin).strip()]
        if not parts:
            raise ValueError("ALLOWED_ORIGINS must contain at least one origin")
        for origin in parts:
            if not origin.startswith(("http://", "https://")):
                raise ValueError("ALLOWED_ORIGINS entries must start with http:// or https://")
            if "*" in origin:
                raise ValueError("Wildcard origins are not allowed")
        return tuple(dict.fromkeys(parts))

    @field_validator("stripe_success_url", "stripe_cancel_url")
    @classmethod
    def validate_stripe_redirect_urls(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise ValueError("Stripe redirect URLs must start with http:// or https://")
        return value

    @field_validator("stripe_price_starter", "stripe_price_pro", "stripe_price_enterprise")
    @classmethod
    def validate_price_ids(cls, value: str | None) -> str | None:
        if value in {None, ""}:
            return None
        if not value.startswith("price_"):
            raise ValueError("Stripe price IDs must start with price_")
        return value

    @field_validator("app_environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"development", "test", "staging", "production"}:
            raise ValueError("APP_ENV must be development, test, staging, or production")
        return normalized

    @cached_property
    def allowed_origin_set(self) -> set[str]:
        return set(self.allowed_origins)

    @cached_property
    def stripe_price_map(self) -> dict[str, str]:
        return {
            tier: price_id
            for tier, price_id in {
                "starter": self.stripe_price_starter,
                "pro": self.stripe_price_pro,
                "enterprise": self.stripe_price_enterprise,
            }.items()
            if price_id
        }


def bool_env(name: str, default: str) -> str:
    return os.environ.get(name, default).strip().lower()


def load_settings_from_env() -> AppSettings:
    try:
        return AppSettings(
            database_url=SecretStr(os.environ.get("DATABASE_URL", "").strip()),
            database_pool_min=os.environ.get("DATABASE_POOL_MIN", "1"),
            database_pool_max=os.environ.get("DATABASE_POOL_MAX", "10"),
            jwt_secret=SecretStr(os.environ.get("JWT_SECRET", "").strip()),
            jwt_ttl_seconds=os.environ.get("JWT_TTL_SECONDS", "1209600"),
            cookie_secure=bool_env("COOKIE_SECURE", "false") in {"1", "true", "yes"},
            allowed_origins=os.environ.get(
                "ALLOWED_ORIGINS",
                "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:8080,http://localhost:8080",
            ),
            rate_limit_auth_per_minute=os.environ.get("RATE_LIMIT_AUTH_PER_MINUTE", "12"),
            rate_limit_api_per_minute=os.environ.get("RATE_LIMIT_API_PER_MINUTE", "120"),
            dashboard_host=os.environ.get("DASHBOARD_HOST", "127.0.0.1"),
            dashboard_port=os.environ.get("DASHBOARD_PORT", "8787"),
            app_environment=os.environ.get("APP_ENV", "development"),
            require_alembic_migrations=bool_env("REQUIRE_ALEMBIC_MIGRATIONS", "false") in {"1", "true", "yes"},
            stripe_secret_key=SecretStr(os.environ["STRIPE_SECRET_KEY"].strip()) if os.environ.get("STRIPE_SECRET_KEY", "").strip() else None,
            stripe_webhook_secret=SecretStr(os.environ["STRIPE_WEBHOOK_SECRET"].strip()) if os.environ.get("STRIPE_WEBHOOK_SECRET", "").strip() else None,
            stripe_success_url=os.environ.get("STRIPE_SUCCESS_URL", "http://127.0.0.1:5173/?checkout=success"),
            stripe_cancel_url=os.environ.get("STRIPE_CANCEL_URL", "http://127.0.0.1:5173/?checkout=cancelled"),
            stripe_price_starter=os.environ.get("STRIPE_PRICE_STARTER") or None,
            stripe_price_pro=os.environ.get("STRIPE_PRICE_PRO") or None,
            stripe_price_enterprise=os.environ.get("STRIPE_PRICE_ENTERPRISE") or None,
        )
    except ValidationError as exc:
        messages = []
        for error in exc.errors(include_input=False):
            field = ".".join(str(part) for part in error["loc"])
            messages.append(f"{field}: {error['msg']}")
        raise RuntimeError("Invalid dashboard configuration: " + "; ".join(messages)) from exc
