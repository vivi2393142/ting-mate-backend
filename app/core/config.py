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
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Speech-to-Text
    assemblyai_api_key: str = ""

    # Gemini (LLM)
    gemini_model_name: str = ""
    gemini_api_key: str = ""

    # Google Places API
    google_place_api_key: str = ""
    google_place_search_api_url: str = ""

    model_config = {
        "env_file": ".env",
        "env_prefix": "TINGMATE_",
        "case_sensitive": False,
    }


def get_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development")

    if env == "production":
        # Load production settings
        settings = Settings(_env_file=".env.prod")
    elif env == "test":
        # Load test settings
        settings = Settings(_env_file=".env.test")
    else:
        # Load development settings
        settings = Settings(_env_file=".env.dev")

    return settings


# Create settings instance
settings = get_settings()
