"""
Test configuration for TingMate backend
"""

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class TestSettings(BaseSettings):
    """Test-specific settings"""

    # Environment
    environment: str = "test"

    # Test database credentials
    test_db_host: str = "localhost"
    test_db_port: int = 3306
    test_db_user: str = "root"
    test_db_password: str = ""

    model_config = ConfigDict(
        env_file=".env.test", extra="ignore"  # Allow extra fields from env file
    )


# Load test settings
test_settings = TestSettings()

# Test database configuration
TEST_DATABASE_NAME = "tingmate_test"
TEST_DB_USER = test_settings.test_db_user
TEST_DB_PASSWORD = test_settings.test_db_password
TEST_DB_HOST = test_settings.test_db_host
TEST_DB_PORT = test_settings.test_db_port
