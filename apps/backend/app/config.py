import os
from datetime import timedelta


class BaseConfig:
    """Shared configuration used by every CADRI runtime environment."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key")

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 10,
        "max_overflow": 20,
    }

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

    MAIL_SERVER = os.getenv("MAIL_SERVER", "mailpit")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 1025))
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "no-reply@cadri.local")

    JWT_TOKEN_LOCATION = ["headers"]
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", 15))
    )

    ACCOUNT_ACTIVATION_TOKEN_EXPIRES_HOURS = int(
        os.getenv("ACCOUNT_ACTIVATION_TOKEN_EXPIRES_HOURS", 24)
    )
    PASSWORD_RESET_TOKEN_EXPIRES_HOURS = int(
        os.getenv("PASSWORD_RESET_TOKEN_EXPIRES_HOURS", 2)
    )
    REFRESH_TOKEN_EXPIRES_DAYS = int(
        os.getenv("REFRESH_TOKEN_EXPIRES_DAYS", 7)
    )

    REFRESH_COOKIE_NAME = os.getenv("REFRESH_COOKIE_NAME", "refresh_token")
    REFRESH_COOKIE_PATH = os.getenv("REFRESH_COOKIE_PATH", "/auth")
    REFRESH_COOKIE_SECURE = os.getenv("REFRESH_COOKIE_SECURE", "false").lower() == "true"
    REFRESH_COOKIE_SAMESITE = os.getenv("REFRESH_COOKIE_SAMESITE", "Lax")


class DevelopmentConfig(BaseConfig):
    """Configuration used when running the application locally."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://cadri_user:cadri_password@db:5432/cadri_db",
    )


class TestingConfig(BaseConfig):
    """Configuration used by automated tests."""

    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://cadri_user:cadri_password@db:5432/cadri_test_db",
    )


class ProductionConfig(BaseConfig):
    """Configuration used by deployed production instances."""

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")


def get_config():
    """Return the configuration class matching the FLASK_ENV value."""
    env = os.getenv("FLASK_ENV", "development")

    config_map = {
        "development": DevelopmentConfig,
        "testing": TestingConfig,
        "production": ProductionConfig,
    }

    return config_map.get(env, DevelopmentConfig)
