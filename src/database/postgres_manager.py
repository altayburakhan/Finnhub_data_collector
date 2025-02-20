from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker  # declarative_base'i buradan import et
from datetime import datetime
import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)

Base = declarative_base()  # Yeni import ile kullan

class StockData(Base):
    __tablename__ = 'stock_data'

    id = Column(Integer, primary_key=True, autoincrement=True)  # autoincrement ekleyelim
    symbol = Column(String(10), nullable=False, index=True)     # index ekleyelim
    price = Column(Float, nullable=False)
    volume = Column(Float)
    timestamp = Column(DateTime, nullable=False, index=True)    # index ekleyelim
    collected_at = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<StockData(symbol='{self.symbol}', price={self.price}, timestamp='{self.timestamp}')>"

class PostgresManager:
    def __init__(self):
        """PostgreSQL bağlantısını başlat"""
        self.engine = None
        self.Session = None
        self.setup_connection()

    def setup_connection(self):
        """Veritabanı bağlantısını yapılandır"""
        try:
            db_url = (
                f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@"
                f"{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
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
        Hisse senedi verisini veritabanına ekle
        
        Args:
            data: Eklenecek veri dictionary'si
            
        Returns:
            Eklenen StockData objesi veya None
        """
        try:
            session = self.Session()
            
            stock_data = StockData(
                symbol=data['symbol'],
                price=data['price'],
                volume=data['volume'],
                timestamp=datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S'),
                collected_at=datetime.fromisoformat(data['collected_at'])
            )
            
            session.add(stock_data)
            session.commit()
            
            # ID'yi loglayalım
            logger.info(f"Veri başarıyla kaydedildi: {data['symbol']}, ID: {stock_data.id}")
            return stock_data
            
        except Exception as e:
            logger.error(f"Veri kaydetme hatası: {e}")
            session.rollback()
            return None
        finally:
            session.close()

    def get_latest_records(self, limit: int = 5) -> list:
        """
        En son kayıtları getir
        
        Args:
            limit: Kaç kayıt getirileceği
            
        Returns:
            StockData listesi
        """
        session = self.Session()
        try:
            records = session.query(StockData)\
                .order_by(StockData.collected_at.desc())\
                .limit(limit)\
                .all()
            return records
        finally:
            session.close()