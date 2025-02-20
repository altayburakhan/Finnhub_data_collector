"""PostgreSQL veritabanı yönetimi için modül."""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Type, Union, cast

from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine, desc
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

logger = logging.getLogger(__name__)

# SQLAlchemy model base'i
BaseType = declarative_base()

# Custom types
StockDataDict = Dict[str, Union[str, float, datetime]]
SessionMaker = Type[sessionmaker[Session]]


class StockData(BaseType):  # type: ignore
    """Hisse senedi verilerini tutan veritabanı modeli."""

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
    """PostgreSQL veritabanı işlemlerini yöneten sınıf."""

    def __init__(self) -> None:
        """Initializes PostgreSQL connection."""
        self.engine: Optional[Engine] = None
        self._session_factory: Optional[SessionMaker] = None
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
            BaseType.metadata.create_all(self.engine)
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
            symbol = cast(str, data["symbol"])
            price = cast(float, data["price"])
            volume = cast(float, data["volume"])
            timestamp_str = cast(str, data["timestamp"])
            collected_at_str = cast(str, data["collected_at"])

            stock_data = StockData(
                symbol=symbol,
                price=price,
                volume=volume,
                timestamp=datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S"),
                collected_at=datetime.fromisoformat(collected_at_str),
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
