#!/usr/bin/env python3
"""
Database initialization script for TingMate backend
This script creates the database and initial tables
"""

import logging
import os
import sys

import mysql.connector
from mysql.connector import Error

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Connect to MySQL server (without specifying database)
        connection = mysql.connector.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            charset=settings.db_charset,
        )

        cursor = connection.cursor()

        # Create database if it doesn't exist
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS {settings.db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        logger.info(f"Database '{settings.db_name}' created or already exists")

        cursor.close()
        connection.close()

    except Error as e:
        logger.error(f"Error creating database: {e}")
        raise


def create_tables():
    """Create initial tables"""
    try:
        from app.core.database import test_connection

        # Test connection first
        if not test_connection():
            logger.error("Cannot connect to database")
            return False

        from app.core.database import execute_update

        # Create users table based on UserDB schema
        users_table_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(36) PRIMARY KEY,
            email VARCHAR(100) UNIQUE,
            anonymous_id VARCHAR(50) UNIQUE,
            hashed_password VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

        # Execute table creation
        execute_update(users_table_sql)
        logger.info("Users table created successfully")

        return True

    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        return False


def main():
    """Main initialization function"""
    logger.info("Starting database initialization...")

    try:
        # Step 1: Create database
        create_database()

        # Step 2: Create tables
        if create_tables():
            logger.info("Tables created successfully")
        else:
            logger.error("Failed to create tables")
            return False

        logger.info("Database initialization completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
