import os

class Settings:
    def __init__(self):
        self.DB_USER = os.getenv("DB_USER", "buska_user")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD", "buska_pass")
        self.DB_HOST = os.getenv("DB_HOST", "localhost")
        self.DB_PORT = os.getenv("DB_PORT", "5432")
        self.DB_NAME = os.getenv("DB_NAME", "buska_db")

        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me")
        self.JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", "2"))

        self.SQLALCHEMY_DATABASE_URI = (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


def get_settings() -> Settings:
    return Settings()
