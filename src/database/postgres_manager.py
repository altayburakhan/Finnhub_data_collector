"""PostgreSQL database manager for stock data.

This module handles all database operations including connection
management and data insertion.
"""

import logging
import os
from datetime import datetime
from typing import Dict, Optional, Union, List, Any

import psycopg2
from dotenv import load_dotenv
from psycopg2 import Error as PostgresError
from psycopg2.extensions import connection, cursor
from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine, text
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

    def __init__(self):
        """Initialize database connection."""
        # Use POSTGRES_ prefixed environment variables
        self.host = os.getenv("POSTGRES_HOST", "localhost")
        self.port = int(os.getenv("POSTGRES_PORT", "5432"))
        self.db_name = os.getenv("POSTGRES_DB", "postgres")
        self.user = os.getenv("POSTGRES_USER", "postgres")
        self.password = os.getenv("POSTGRES_PASSWORD", "postgres")

        try:
            # Create SQLAlchemy engine and session
            self.database_url = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}"
            logger.info(f"Connecting to database at {self.host}:{self.port}")
            self.engine = create_engine(self.database_url)
            self.Session = sessionmaker(bind=self.engine)

            # Create tables
            Base.metadata.create_all(self.engine)
            logger.info("Database initialization successful")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise

    def connect(self) -> None:
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.db_name,
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

    def insert_stock_data(self, data: Dict[str, Any]) -> Optional[bool]:
        try:
            # Validate data before insertion
            if not self._validate_stock_data(data):
                logger.error(f"❌ Data validation failed. Missing or invalid fields in: {data}")
                return None

            # Convert timestamp string to datetime if it's a string
            if isinstance(data["timestamp"], str):
                try:
                    data["timestamp"] = datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S")
                    logger.debug(f"Converted timestamp: {data['timestamp']}")
                except ValueError as e:
                    logger.error(f"❌ Timestamp conversion error for {data['symbol']}: {e}")
                    logger.error(f"Problematic timestamp: {data['timestamp']}")
                    return None

            # Convert collected_at to datetime if it's a string
            if isinstance(data["collected_at"], str):
                try:
                    data["collected_at"] = datetime.strptime(data["collected_at"], "%Y-%m-%d %H:%M:%S")
                    logger.debug(f"Converted collected_at: {data['collected_at']}")
                except ValueError as e:
                    logger.error(f"❌ Collected_at conversion error for {data['symbol']}: {e}")
                    logger.error(f"Problematic collected_at: {data['collected_at']}")
                    return None

            session = self.Session()
            try:
                stock_data = StockData(
                    symbol=str(data["symbol"]),
                    price=float(data["price"]),
                    volume=float(data["volume"]),
                    timestamp=data["timestamp"],
                    collected_at=data["collected_at"]
                )
                session.add(stock_data)
                session.commit()
                logger.info(f"✅ Successfully inserted {data['symbol']} data into database")
                return True
            except Exception as e:
                session.rollback()
                logger.error(f"❌ Database insertion error for {data['symbol']}: {e}")
                return None
            finally:
                session.close()
        except Exception as e:
            logger.error(f"❌ General error in insert_stock_data: {e}")
            logger.error(f"Problematic data: {data}")
            return None

    def _validate_stock_data(self, data: Dict[str, Any]) -> bool:
        """Validate stock data before insertion.

        Args:
            data: Stock data to validate

        Returns:
            bool: Whether the data is valid
        """
        required_fields = ["symbol", "price", "volume", "timestamp", "collected_at"]
        
        # Check if all required fields exist
        if not all(field in data for field in required_fields):
            logger.error(f"Missing fields in data: {data}")
            return False
        
        # Validate data types
        try:
            float(data["price"])
            float(data["volume"])
            str(data["symbol"])
            return True
        except (ValueError, TypeError) as e:
            logger.error(f"Data type validation error: {e}")
            return False

    def close(self) -> None:
        """Close database connection and cursor."""
        try:
            if self.cur:
                self.cur.close()
            if self.conn:
                self.conn.close()
        except PostgresError as e:
            logger.error(f"Error closing database connection: {e}")

    def get_latest_records(self, limit: int = 10) -> List[Dict[str, Any]]:
        session = self.Session()
        try:
            records = session.query(StockData)\
                .order_by(StockData.timestamp.desc())\
                .limit(limit)\
                .all()
            
            return [
                {
                    "symbol": record.symbol,
                    "price": record.price,
                    "volume": record.volume,
                    "timestamp": record.timestamp,
                    "collected_at": record.collected_at
                }
                for record in records
            ]
        finally:
            session.close()
