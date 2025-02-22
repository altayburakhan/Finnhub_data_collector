"""Module for testing database connection."""

import logging
import os
from typing import Optional, Tuple

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine.base import Engine

logger = logging.getLogger(__name__)

load_dotenv()


def get_db_connection() -> Optional[Engine]:
    """
    Create database connection.

    Returns:
        Optional[Engine]: SQLAlchemy engine object or None
    """
    try:
        db_url = (
            f"postgresql://{os.getenv('POSTGRES_USER')}:"
            f"{os.getenv('POSTGRES_PASSWORD')}@"
            f"{os.getenv('POSTGRES_HOST')}:"
            f"{os.getenv('POSTGRES_PORT')}/"
            f"{os.getenv('POSTGRES_DB')}"
        )
        return create_engine(db_url)
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return None


def test_connection(engine: Engine) -> Tuple[bool, str]:
    """
    Test database connection.

    Args:
        engine: SQLAlchemy engine object

    Returns:
        Tuple[bool, str]: (Success, Message)
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.scalar()

            result = conn.execute(
                text(
                    """
                SELECT count(*)
                FROM information_schema.tables
                WHERE table_schema = 'public';
            """
                )
            )
            table_count = result.scalar()

        return True, (
            f"Connection successful!\n"
            f"PostgreSQL Version: {version}\n"
            f"Table Count: {table_count}"
        )

    except Exception as e:
        error_msg = f"Connection error: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def check_table_exists(engine: Engine, table_name: str) -> bool:
    """
    Check if the specified table exists.

    Args:
        engine: SQLAlchemy engine object
        table_name: Table name to check

    Returns:
        bool: True if table exists, False otherwise
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = :table_name
                );
            """
                ),
                {"table_name": table_name},
            )
            exists: bool = bool(result.scalar())
            return exists
    except Exception as e:
        logger.error(f"Table check error: {str(e)}")
        return False


def main() -> None:
    """Main application function."""
    engine = get_db_connection()
    if not engine:
        logger.error("Database connection could not be created!")
        return

    success, message = test_connection(engine)
    if success:
        logger.info(message)

        if check_table_exists(engine, "stock_data"):
            logger.info("stock_data table exists")
        else:
            logger.warning("stock_data table not found!")
    else:
        logger.error(message)


if __name__ == "__main__":
    main()
