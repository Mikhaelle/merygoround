"""Application settings loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env file.

    Attributes:
        DATABASE_URL: PostgreSQL async connection string.
        JWT_SECRET_KEY: Secret key for signing JWT tokens.
        JWT_ALGORITHM: JWT signing algorithm.
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES: Access token TTL.
        JWT_REFRESH_TOKEN_EXPIRE_DAYS: Refresh token TTL.
        VAPID_PRIVATE_KEY: VAPID private key for web push.
        VAPID_PUBLIC_KEY: VAPID public key for web push.
        VAPID_CLAIMS_EMAIL: Contact email for VAPID claims.
        CORS_ORIGINS: Comma-separated list of allowed CORS origins.
        ENVIRONMENT: Deployment environment name.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/merygoround"
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    VAPID_PRIVATE_KEY: str = ""
    VAPID_PUBLIC_KEY: str = ""
    VAPID_CLAIMS_EMAIL: str = "mailto:admin@merygoround.app"
    CORS_ORIGINS: str = "http://localhost:3000"
    ENVIRONMENT: str = "development"
    APP_TIMEZONE: str = "America/Sao_Paulo"
