#!/usr/bin/env python3
"""
Simple test runner for TingMate backend
"""

import os
import subprocess
import sys

import mysql.connector

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings  # noqa: E402
from tests.test_config import TEST_DATABASE_NAME  # noqa: E402


def setup_db():
    """Setup test database"""
    print("🔧 Setting up test database...")

    try:
        connection = mysql.connector.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
        )

        cursor = connection.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS {TEST_DATABASE_NAME}")
        cursor.execute(f"CREATE DATABASE {TEST_DATABASE_NAME}")
        cursor.close()
        connection.close()

        # Initialize tables
        subprocess.run(["python3", "scripts/init_db.py"], check=True)
        print("✅ Test database ready")
        return True

    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False


def run_pytest():
    """Run pytest with consistent options"""
    return subprocess.run(
        [
            "python3",
            "-m",
            "pytest",
            "tests/",
            "-v",
            "--tb=short",
            "--disable-warnings",
            "--color=yes",
        ]
    )


def cleanup_db():
    """Cleanup test database"""
    print("🧹 Cleaning up test database...")

    try:
        connection = mysql.connector.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
        )

        cursor = connection.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS {TEST_DATABASE_NAME}")
        connection.commit()
        cursor.close()
        connection.close()
        print("✅ Test database removed")

    except Exception as e:
        print(f"❌ Cleanup failed: {e}")


def main():
    """Main test runner"""
    keep_db = "--keep-db" in sys.argv

    print("🚀 Starting test run...")

    # Setup database
    if not setup_db():
        sys.exit(1)

    # Run tests
    print("🧪 Running tests...")
    result = run_pytest()

    # Cleanup (unless keeping database)
    if not keep_db:
        cleanup_db()
    else:
        print("💡 Test database kept for inspection")

    # Report result
    if result.returncode == 0:
        print("🎉 All tests passed!")
    else:
        print("💥 Some tests failed!")

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
