"""My PostgreSQL database management module.

This is where I handle all database operations using SQLAlchemy ORM.
It's my first time using an ORM, and I've learned a lot about
database management through this project.
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, TypeVar, Union

from dotenv import load_dotenv
from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine, desc
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

logger = logging.getLogger(__name__)
load_dotenv()


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


T = TypeVar("T", bound=Session)
SessionFactory = sessionmaker[T]

StockDataDict = Dict[str, Union[str, float, datetime]]


class StockData(Base):
    """My model class for storing stock data.

    Each row represents a trade with important information like
    symbol, price, volume, and timestamps.
    """

    __tablename__ = "stock_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)
    price = Column(Float, nullable=False)
    volume = Column(Float)
    timestamp = Column(DateTime, nullable=False, index=True)
    collected_at = Column(DateTime, nullable=False)

    def __init__(self, **kwargs: Union[str, float, datetime, None]) -> None:
        """Initialize the model with provided values."""
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return (
            f"<StockData(symbol='{self.symbol}', "
            f"price={self.price}, "
            f"timestamp='{self.timestamp}')>"
        )


class PostgresManager:
    """My main class for managing database operations.

    I handle all core database operations here, including connection
    management, data insertion, and querying.
    """

    def __init__(self) -> None:
        """Set up database connection and session factory."""
        self.engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker[Session]] = None
        self.Session: Optional[sessionmaker[Session]] = None
        self.setup_connection()

    def setup_connection(self) -> None:
        """Establish database connection and create tables."""
        try:
            db_url = (
                f"postgresql://{os.getenv('POSTGRES_USER')}:"
                f"{os.getenv('POSTGRES_PASSWORD')}@"
                f"{os.getenv('POSTGRES_HOST')}:"
                f"{os.getenv('POSTGRES_PORT')}/"
                f"{os.getenv('POSTGRES_DB')}"
            )
            self.engine = create_engine(db_url)
            self._session_factory = sessionmaker(bind=self.engine)
            self.Session = self._session_factory
            Base.metadata.create_all(self.engine)
            logger.info("PostgreSQL connection established successfully")
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise

    def _get_session(self) -> Session:
        """Create a new database session."""
        if not self._session_factory:
            raise RuntimeError("Database connection not established")
        return self._session_factory()

    def insert_stock_data(self, data: StockDataDict) -> Optional[StockData]:
        """Insert stock data into the database.

        Args:
            data: Data dictionary to insert
                Required fields:
                - symbol: str
                - price: float
                - volume: float
                - timestamp: str (format: '%Y-%m-%d %H:%M:%S')
                - collected_at: str (ISO format)

        Returns:
            Optional[StockData]: Inserted data object or None if failed
        """
        session = self._get_session()
        try:
            if not isinstance(data.get("symbol"), str):
                raise ValueError("Symbol must be a string")
            if (
                not isinstance(data.get("price"), (int, float))
                and not str(data.get("price", "")).replace(".", "").isdigit()
            ):
                raise ValueError("Price must be a number")
            if data.get("volume") is not None and not isinstance(
                data.get("volume"), (int, float)
            ):
                raise ValueError("Volume must be a number or None")

            symbol = str(data["symbol"])
            if len(symbol) > 10:
                raise ValueError("Symbol length must be 10 characters or less")

            try:
                price = float(str(data["price"]))
            except (ValueError, TypeError):
                raise ValueError("Invalid price format")

            volume = None
            if data.get("volume") is not None:
                try:
                    volume = float(str(data["volume"]))
                except (ValueError, TypeError):
                    raise ValueError("Invalid volume format")

            timestamp_str = str(data["timestamp"])
            collected_at_str = str(data["collected_at"])

            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise ValueError("Invalid timestamp format")

            try:
                collected_at = datetime.fromisoformat(collected_at_str)
            except ValueError:
                raise ValueError("Invalid collected_at format")

            stock_data = StockData(
                symbol=symbol,
                price=price,
                volume=volume,
                timestamp=timestamp,
                collected_at=collected_at,
            )

            session.add(stock_data)
            session.commit()

            logger.info(f"Data saved successfully: {symbol}, ID: {stock_data.id}")
            return stock_data

        except Exception as e:
            logger.error(f"Data insertion error: {e}")
            session.rollback()
            return None
        finally:
            session.close()

    def get_latest_records(self, limit: int = 5) -> List[StockData]:
        """Get the most recent records from the database.

        Args:
            limit: Number of records to retrieve

        Returns:
            List[StockData]: List of StockData objects
        """
        session = self._get_session()
        try:
            records = (
                session.query(StockData)
                .order_by(desc(StockData.collected_at))
                .limit(limit)
                .all()
            )
            return list(records)
        finally:
            session.close()
