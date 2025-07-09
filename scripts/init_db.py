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

from app.core.config import settings  # noqa: E402

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_database_name():
    """Get database name based on environment"""
    env = os.getenv("ENVIRONMENT", "development")
    if env == "test":
        return "tingmate_test"
    return settings.db_name


def create_database():
    """Create the database if it doesn't exist"""
    try:
        db_name = get_database_name()

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
            f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"  # noqa: E501
        )
        logger.info(f"Database '{db_name}' created or already exists")

        cursor.close()
        connection.close()

    except Error as e:
        logger.error(f"Error creating database: {e}")
        raise


def create_tables(engine=None):
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
            id VARCHAR(36) PRIMARY KEY, -- Provided by frontend, must be valid UUID
            email VARCHAR(100) UNIQUE,
            hashed_password VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

        # Create user_settings table
        user_settings_table_sql = """
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id VARCHAR(36) PRIMARY KEY,
            text_size ENUM('STANDARD', 'LARGE') DEFAULT 'STANDARD',
            display_mode ENUM('FULL', 'SIMPLE') DEFAULT 'FULL',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

        # Create tasks table
        tasks_table_sql = """
        CREATE TABLE IF NOT EXISTS tasks (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL,
            title VARCHAR(255) NOT NULL,
            icon VARCHAR(20) NOT NULL,
            reminder_hour INT NOT NULL CHECK (reminder_hour >= 0 AND reminder_hour <= 23),
            reminder_minute INT NOT NULL CHECK (reminder_minute >= 0 AND reminder_minute <= 59),
            recurrence_interval INT,
            recurrence_unit ENUM('DAY', 'WEEK', 'MONTH'),
            recurrence_days_of_week JSON,
            recurrence_days_of_month JSON,
            completed BOOLEAN DEFAULT FALSE,
            completed_at TIMESTAMP NULL,
            completed_by VARCHAR(36) NULL,
            deleted BOOLEAN DEFAULT FALSE,
            created_by VARCHAR(36) NOT NULL,
            updated_by VARCHAR(36) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (completed_by) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_tasks_user_id (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

        # Create activity_logs table
        activity_logs_table_sql = """
        CREATE TABLE IF NOT EXISTS activity_logs (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL,
            action VARCHAR(50) NOT NULL,
            detail JSON,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_logs_user_id (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

        # Create llm_logs table
        llm_logs_table_sql = """
        CREATE TABLE IF NOT EXISTS llm_logs (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(255) NULL COMMENT 'User ID (optional)',
            conversation_id VARCHAR(255) NULL COMMENT 'Conversation ID (optional)',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            input_text TEXT NOT NULL COMMENT 'User input to LLM',
            output_text TEXT NULL COMMENT 'LLM response (NULL if failed)',
            INDEX idx_user_id (user_id),
            INDEX idx_conversation_id (conversation_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

        # Create assistant_pending_tasks table
        assistant_pending_tasks_table_sql = """
        CREATE TABLE IF NOT EXISTS assistant_pending_tasks (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            conversation_id VARCHAR(255) NOT NULL,
            user_id VARCHAR(36) NOT NULL,
            intent_type ENUM('CREATE_TASK', 'UPDATE_TASK', 'DELETE_TASK') NOT NULL,
            task_data JSON NOT NULL COMMENT 'Task data for the pending operation',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_conversation_id (conversation_id),
            INDEX idx_user_id (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

        # Create assistant_conversations table
        assistant_conversations_table_sql = """
        CREATE TABLE IF NOT EXISTS assistant_conversations (
            conversation_id VARCHAR(255) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL,
            intent_type VARCHAR(50) NULL,
            llm_result JSON NULL,
            turn_count INT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_user_id (user_id),
            INDEX idx_updated_at (updated_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

        # Execute table creation
        execute_update(users_table_sql)
        logger.info("Users table created successfully")

        execute_update(user_settings_table_sql)
        logger.info("User settings table created successfully")

        execute_update(tasks_table_sql)
        logger.info("Tasks table created successfully")

        execute_update(activity_logs_table_sql)
        logger.info("Activity logs table created successfully")

        execute_update(llm_logs_table_sql)
        logger.info("LLM logs table created successfully")

        execute_update(assistant_pending_tasks_table_sql)
        logger.info("Assistant pending tasks table created successfully")

        execute_update(assistant_conversations_table_sql)
        logger.info("Assistant conversations table created successfully")

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
