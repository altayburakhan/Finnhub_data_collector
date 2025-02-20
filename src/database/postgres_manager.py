"""PostgreSQL veritabanı yönetimi için modül."""

from datetime import datetime
import logging
import os
from typing import Dict, List, Optional

from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

Base = declarative_base()


class StockData(Base):
    """Hisse senedi verilerini tutan veritabanı modeli."""

    __tablename__ = 'stock_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)
    price = Column(Float, nullable=False)
    volume = Column(Float)
    timestamp = Column(DateTime, nullable=False, index=True)
    collected_at = Column(DateTime, nullable=False)

    def __repr__(self) -> str:
        """Model string temsili."""
        return (
            f"<StockData(symbol='{self.symbol}', "
            f"price={self.price}, "
            f"timestamp='{self.timestamp}')>"
        )


class PostgresManager:
    """PostgreSQL veritabanı işlemlerini yöneten sınıf."""

    def __init__(self) -> None:
        """PostgreSQL bağlantısını başlat."""
        self.engine = None
        self.Session = None
        self.setup_connection()

    def setup_connection(self) -> None:
        """Veritabanı bağlantısını yapılandır."""
        try:
            db_url = (
                f"postgresql://{os.getenv('POSTGRES_USER')}:"
                f"{os.getenv('POSTGRES_PASSWORD')}@"
                f"{os.getenv('POSTGRES_HOST')}:"
                f"{os.getenv('POSTGRES_PORT')}/"
                f"{os.getenv('POSTGRES_DB')}"
            )
            self.engine = create_engine(db_url)
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
            logger.info("PostgreSQL bağlantısı başarıyla kuruldu")
        except Exception as e:
            logger.error(f"Veritabanı bağlantı hatası: {e}")
            raise

    def insert_stock_data(self, data: Dict) -> Optional[StockData]:
        """
        Hisse senedi verisini veritabanına ekle.

        Args:
            data: Eklenecek veri sözlüğü.
                Gerekli alanlar:
                - symbol: str
                - price: float
                - volume: float
                - timestamp: str ('%Y-%m-%d %H:%M:%S' formatında)
                - collected_at: str (ISO format)

        Returns:
            Optional[StockData]: Eklenen veri objesi veya None
        """
        session = self.Session()
        try:
            stock_data = StockData(
                symbol=data['symbol'],
                price=data['price'],
                volume=data['volume'],
                timestamp=datetime.strptime(
                    data['timestamp'],
                    '%Y-%m-%d %H:%M:%S'
                ),
                collected_at=datetime.fromisoformat(data['collected_at'])
            )

            session.add(stock_data)
            session.commit()

            logger.info(
                f"Veri başarıyla kaydedildi: {data['symbol']}, "
                f"ID: {stock_data.id}"
            )
            return stock_data

        except Exception as e:
            logger.error(f"Veri kaydetme hatası: {e}")
            session.rollback()
            return None
        finally:
            session.close()

    def get_latest_records(self, limit: int = 5) -> List[StockData]:
        """
        En son kayıtları getir.

        Args:
            limit: Kaç kayıt getirileceği

        Returns:
            List[StockData]: StockData nesnelerinin listesi
        """
        session = self.Session()
        try:
            records = session.query(StockData) \
                .order_by(StockData.collected_at.desc(), StockData.price.desc()) \
                .limit(limit) \
                .all()
            return records
        finally:
            session.close()