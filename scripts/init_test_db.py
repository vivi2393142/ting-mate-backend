#!/usr/bin/env python3
"""
Initialize test database separately
"""

import os
import subprocess
import sys

import mysql.connector
from mysql.connector import Error

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings  # noqa: E402
from tests.test_config import TEST_DATABASE_NAME  # noqa: E402


def setup_test_database():
    """Create test database"""
    print("🔧 Setting up test database...")

    try:
        connection = mysql.connector.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
        )

        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute(f"DROP DATABASE IF EXISTS {TEST_DATABASE_NAME}")
            cursor.execute(f"CREATE DATABASE {TEST_DATABASE_NAME}")
            cursor.close()
            connection.close()

            # Initialize tables
            result = subprocess.run(
                ["python3", "scripts/init_db.py"], capture_output=True, text=True
            )

            if result.returncode == 0:
                print("✅ Test database initialized successfully")
                return True
            else:
                print(f"❌ Failed to initialize test database: {result.stderr}")
                return False

    except Error as e:
        print(f"❌ Error setting up test database: {e}")
        return False


def main():
    """Main initialization function"""
    if setup_test_database():
        print("🎉 Test database setup completed!")
    else:
        print("💥 Test database setup failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
