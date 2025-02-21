"""Module for PostgreSQL database management."""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Type, Union, cast

from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine, desc
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

logger = logging.getLogger(__name__)

# SQLAlchemy base model
Base = declarative_base()

# Custom types
StockDataDict = Dict[str, Union[str, float, datetime]]
SessionMaker = Type[sessionmaker[Session]]


class StockData(Base):  # type: ignore
    """Database model for stock data."""

    __tablename__ = "stock_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)
    price = Column(Float, nullable=False)
    volume = Column(Float)
    timestamp = Column(DateTime, nullable=False, index=True)
    collected_at = Column(DateTime, nullable=False)

    def __repr__(self) -> str:
        """Returns string representation of the model."""
        return (
            f"<StockData(symbol='{self.symbol}', "
            f"price={self.price}, "
            f"timestamp='{self.timestamp}')>"
        )


class PostgresManager:
    """Class for managing PostgreSQL database operations."""

    def __init__(self) -> None:
        """Initializes PostgreSQL connection."""
        self.engine: Optional[Engine] = None
        self._session_factory: Optional[SessionMaker] = None
        self.Session: Optional[SessionMaker] = None
        self.setup_connection()

    def setup_connection(self) -> None:
        """Configures database connection."""
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
        """Creates a new session."""
        if not self._session_factory:
            raise RuntimeError("Database connection not established")
        return self._session_factory()

    def insert_stock_data(self, data: StockDataDict) -> Optional[StockData]:
        """
        Inserts stock data into database.

        Args:
            data: Data dictionary to insert.
                Required fields:
                - symbol: str
                - price: float
                - volume: float
                - timestamp: str ('%Y-%m-%d %H:%M:%S' format)
                - collected_at: str (ISO format)

        Returns:
            Optional[StockData]: Inserted data object or None
        """
        session = self._get_session()
        try:
            # Validate data types before casting
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

            symbol = cast(str, data["symbol"])
            if len(symbol) > 10:
                raise ValueError("Symbol length must be 10 characters or less")

            # Try to convert price to float
            try:
                price = float(cast(Union[str, float], data["price"]))
            except (ValueError, TypeError):
                raise ValueError("Invalid price format")

            # Handle volume (can be None)
            volume = None
            if data.get("volume") is not None:
                try:
                    volume = float(cast(Union[str, float], data["volume"]))
                except (ValueError, TypeError):
                    raise ValueError("Invalid volume format")

            # Validate and parse timestamps
            timestamp_str = cast(str, data["timestamp"])
            collected_at_str = cast(str, data["collected_at"])

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
        """
        Retrieves latest records.

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
