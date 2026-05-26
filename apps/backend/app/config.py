import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-too")

    JWT_TOKEN_LOCATION = ["headers"]
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", 15))
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

    MAIL_SERVER = os.getenv("MAIL_SERVER", "mailpit")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 1025))
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "no-reply@cadri.local")

    ACCOUNT_ACTIVATION_TOKEN_EXPIRES_HOURS = int(
        os.getenv("ACCOUNT_ACTIVATION_TOKEN_EXPIRES_HOURS", 24)
    )
    PASSWORD_RESET_TOKEN_EXPIRES_HOURS = int(
        os.getenv("PASSWORD_RESET_TOKEN_EXPIRES_HOURS", 2)
    )


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://cadri_user:cadri_password@db:5432/cadri_db",
    )


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://cadri_user:cadri_password@db:5432/cadri_test_db",
    )


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
