"""Module for resetting and recreating the database."""

import logging
import os
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine.base import Engine

# Log configuration
logger = logging.getLogger(__name__)

# Load .env file
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


def reset_database(engine: Engine) -> bool:
    """
    Reset database and recreate tables.

    Args:
        engine: SQLAlchemy engine object

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Close existing connections
        with engine.connect() as conn:
            conn.execute(
                text(
                    """
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = current_database()
                AND pid <> pg_backend_pid();
            """
                )
            )
            conn.commit()

        # Drop tables
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS stock_data CASCADE;"))
            conn.commit()

        # Create new table
        with engine.connect() as conn:
            conn.execute(
                text(
                    """
                CREATE TABLE stock_data (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(10) NOT NULL,
                    price FLOAT NOT NULL,
                    volume FLOAT,
                    timestamp TIMESTAMP NOT NULL,
                    collected_at TIMESTAMP NOT NULL
                );
            """
                )
            )

            # Create indexes
            conn.execute(
                text(
                    """
                CREATE INDEX idx_stock_symbol
                ON stock_data(symbol);
            """
                )
            )
            conn.execute(
                text(
                    """
                CREATE INDEX idx_stock_timestamp
                ON stock_data(timestamp);
            """
                )
            )
            conn.commit()

        logger.info("Database reset successfully")
        return True

    except Exception as e:
        logger.error(f"Database reset error: {str(e)}")
        return False


def main() -> None:
    """Main application function."""
    engine = get_db_connection()
    if not engine:
        logger.error("Database connection could not be created!")
        return

    if reset_database(engine):
        logger.info("Database reset successful")
    else:
        logger.error("Database reset failed!")


if __name__ == "__main__":
    main()
