import os
import logging

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when required configuration is missing."""
    pass


class Settings:
    def __init__(self):
        # Database settings (with development defaults)
        self.DB_USER = os.getenv("DB_USER", "buska_user")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD", "buska_pass")
        self.DB_HOST = os.getenv("DB_HOST", "localhost")
        self.DB_PORT = os.getenv("DB_PORT", "5432")
        self.DB_NAME = os.getenv("DB_NAME", "buska_db")

        # JWT settings (secret is required)
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
        if not self.JWT_SECRET_KEY:
            raise ConfigurationError(
                "JWT_SECRET_KEY environment variable is required. "
                "Set it to a secure random string."
            )
        
        if self.JWT_SECRET_KEY == "change-me":
            logger.warning(
                "JWT_SECRET_KEY is set to 'change-me'. "
                "Use a secure random string in production!"
            )

        self.JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", "2"))

        # Database URI
        self.SQLALCHEMY_DATABASE_URI = (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


# Module-level instance (created once at import time)
settings = Settings()
