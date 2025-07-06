#!/usr/bin/env python3
"""
Clean up test database manually
"""

import os
import sys

import mysql.connector
from mysql.connector import Error

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings  # noqa: E402
from tests.test_config import TEST_DATABASE_NAME  # noqa: E402


def cleanup_test_database():
    """Remove test database"""
    print("🧹 Cleaning up test database...")

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
            connection.commit()
            cursor.close()
            connection.close()
            print("✅ Test database removed")
            return True

    except Error as e:
        print(f"❌ Error cleaning up test database: {e}")
        return False


def main():
    """Main cleanup function"""
    if cleanup_test_database():
        print("🎉 Cleanup completed successfully!")
    else:
        print("💥 Cleanup failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
