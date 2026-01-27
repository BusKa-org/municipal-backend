import logging
import os

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when required configuration is missing."""

    pass


class Settings:
    def __init__(self):
        # Environment
        self.ENV = os.getenv("FLASK_ENV", "development")
        self.DEBUG = self.ENV == "development"

        # Database settings (with development defaults)
        self.DB_USER = os.getenv("DB_USER", "buska_user")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD", "buska_pass")
        self.DB_HOST = os.getenv("DB_HOST", "localhost")
        self.DB_PORT = os.getenv("DB_PORT", "5432")
        self.DB_NAME = os.getenv("DB_NAME", "buska_db")

        # JWT settings
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me")
        if self.JWT_SECRET_KEY == "change-me":
            logger.warning(
                "JWT_SECRET_KEY is set to 'change-me'. " "Use a secure random string in production!"
            )
        self.JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", "2"))

        # CORS settings
        # Comma-separated list of allowed origins, or "*" for all (dev only)
        # Example: "https://app.buska.com,https://admin.buska.com"
        cors_origins_raw = os.getenv("CORS_ORIGINS", "")
        if cors_origins_raw:
            self.CORS_ORIGINS: list[str] | str = [
                origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()
            ]
        elif self.DEBUG:
            # Allow all origins in development
            self.CORS_ORIGINS = "*"
        else:
            # Restrictive default for production
            self.CORS_ORIGINS = []
            logger.warning(
                "CORS_ORIGINS not set in production. " "No cross-origin requests will be allowed."
            )

        # Database URI
        self.SQLALCHEMY_DATABASE_URI = (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


# Module-level instance (created once at import time)
settings = Settings()
