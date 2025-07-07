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

    # Google Cloud
    google_cloud_project_id: str = ""
    google_cloud_credentials_file: str = ""
    google_cloud_region: str = "us-central1"

    # Speech-to-Text
    speech_to_text_language_code: str = "en-US"
    speech_to_text_encoding: str = "LINEAR16"
    speech_to_text_sample_rate_hertz: int = 16000

    # Vertex AI (Gemini)
    vertex_ai_location: str = "us-central1"
    vertex_ai_model_name: str = "gemini-1.5-flash"
    vertex_ai_max_tokens: int = 1024
    vertex_ai_temperature: float = 0.1

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
