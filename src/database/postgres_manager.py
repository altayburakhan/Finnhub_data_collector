"""PostgreSQL database manager for stock data.

This module handles all database operations including connection
management and data insertion.
"""

import logging
import os
from datetime import datetime
from typing import Dict, Optional, Union

import psycopg2
from dotenv import load_dotenv
from psycopg2 import Error as PostgresError
from psycopg2.extensions import connection, cursor
from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Type hint for stock data dictionary
StockDataDict = Dict[str, Union[str, float, datetime]]

# Using new SQLAlchemy 2.0 style
Base = declarative_base()

class StockData(Base):
    __tablename__ = 'stock_data'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String)
    price = Column(Float)
    volume = Column(Float)
    timestamp = Column(DateTime)
    collected_at = Column(DateTime)

class PostgresManager:
    """Manages PostgreSQL database operations."""

    def __init__(self) -> None:
        """Initialize database connection parameters."""
        self.host: str = os.getenv("DB_HOST", "localhost")
        self.port: str = os.getenv("DB_PORT", "5432")
        self.dbname: str = os.getenv("DB_NAME", "postgres")
        self.user: str = os.getenv("DB_USER", "postgres")
        self.password: str = os.getenv("DB_PASSWORD", "")
        self.conn: Optional[connection] = None
        self.cur: Optional[cursor] = None
        self.create_table()

    def connect(self) -> None:
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.dbname,
                user=self.user,
                password=self.password
            )
            self.cur = self.conn.cursor()
            logger.info("Successfully connected to PostgreSQL database")
        except PostgresError as e:
            logger.error(f"Error connecting to PostgreSQL database: {e}")
            raise

    def create_table(self) -> None:
        """Create stock data table if it doesn't exist."""
        try:
            self.connect()
            if self.cur:
                self.cur.execute("""
                    CREATE TABLE IF NOT EXISTS stock_data (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(10) NOT NULL,
                        price DECIMAL(10,2) NOT NULL,
                        volume DECIMAL(15,2) NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        collected_at TIMESTAMP NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_symbol_timestamp 
                    ON stock_data(symbol, timestamp);
                """)
                if self.conn:
                    self.conn.commit()
                logger.info("Stock data table created/verified successfully")
        except PostgresError as e:
            logger.error(f"Error creating table: {e}")
            raise
        finally:
            self.close()

    def insert_stock_data(
        self, data: Dict[str, Union[str, float, datetime]]
    ) -> bool:
        """Insert stock data into database.

        Args:
            data: Dictionary containing stock data

        Returns:
            bool: True if insertion successful, False otherwise
        """
        try:
            self.connect()
            if self.cur:
                self.cur.execute("""
                    INSERT INTO stock_data 
                    (symbol, price, volume, timestamp, collected_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    data["symbol"],
                    data["price"],
                    data["volume"],
                    data["timestamp"],
                    data["collected_at"]
                ))
                if self.conn:
                    self.conn.commit()
                return True
        except PostgresError as e:
            logger.error(f"Error inserting data: {e}")
            if self.conn:
                self.conn.rollback()
            return False
        finally:
            self.close()

    def close(self) -> None:
        """Close database connection and cursor."""
        try:
            if self.cur:
                self.cur.close()
            if self.conn:
                self.conn.close()
        except PostgresError as e:
            logger.error(f"Error closing database connection: {e}")
