import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Environment
    environment: str = "development"
    debug: bool = True

    # Database
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "tingmate_dev"
    db_user: str = "root"
    db_password: str = ""
    db_charset: str = "utf8mb4"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    # Security
    secret_key: str = "your_secret_key_here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


def get_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development")

    if env == "production":
        # Load production settings
        settings = Settings(_env_file=".env.prod")
    else:
        # Load development settings
        settings = Settings(_env_file=".env.dev")

    return settings


# Create settings instance
settings = get_settings()
