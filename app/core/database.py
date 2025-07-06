import logging

import mysql.connector

from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_connection() -> bool:
    """Test database connection"""
    try:
        connection = mysql.connector.connect(
            host=settings.db_host,
            port=settings.db_port,
            database=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
            charset=settings.db_charset,
        )
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        connection.close()
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


def execute_query(query: str, params: tuple = None):
    """Execute a query and return results"""
    try:
        connection = mysql.connector.connect(
            host=settings.db_host,
            port=settings.db_port,
            database=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
            charset=settings.db_charset,
        )
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        result = cursor.fetchall()
        cursor.close()
        connection.close()
        return result
    except Exception as e:
        logger.error(f"Query execution error: {e}")
        raise


def execute_update(query: str, params: tuple = None) -> int:
    """Execute an update query and return affected rows"""
    try:
        connection = mysql.connector.connect(
            host=settings.db_host,
            port=settings.db_port,
            database=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
            charset=settings.db_charset,
        )
        cursor = connection.cursor()
        cursor.execute(query, params or ())
        affected_rows = cursor.rowcount
        connection.commit()
        cursor.close()
        connection.close()
        return affected_rows
    except Exception as e:
        logger.error(f"Update execution error: {e}")
        raise
