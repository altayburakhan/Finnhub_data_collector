"""Veritabanını sıfırlama ve yeniden oluşturma modülü."""

import logging
import os
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine.base import Engine

# Log yapılandırması
logger = logging.getLogger(__name__)

# .env dosyasını yükle
load_dotenv()


def get_db_connection() -> Optional[Engine]:
    """
    Veritabanı bağlantısı oluştur.

    Returns:
        Optional[Engine]: SQLAlchemy engine objesi veya None
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
        logger.error(f"Veritabanı bağlantı hatası: {str(e)}")
        return None


def reset_database(engine: Engine) -> bool:
    """
    Veritabanını sıfırla ve tabloları yeniden oluştur.

    Args:
        engine: SQLAlchemy engine objesi

    Returns:
        bool: İşlem başarılı ise True, değilse False
    """
    try:
        # Mevcut bağlantıları kapat
        with engine.connect() as conn:
            conn.execute(text("""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = current_database()
                AND pid <> pg_backend_pid();
            """))
            conn.commit()

        # Tabloları sil
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS stock_data CASCADE;"))
            conn.commit()

        # Yeni tabloyu oluştur
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE stock_data (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(10) NOT NULL,
                    price FLOAT NOT NULL,
                    volume FLOAT,
                    timestamp TIMESTAMP NOT NULL,
                    collected_at TIMESTAMP NOT NULL
                );
            """))
            
            # İndexleri oluştur
            conn.execute(text("""
                CREATE INDEX idx_stock_symbol 
                ON stock_data(symbol);
            """))
            conn.execute(text("""
                CREATE INDEX idx_stock_timestamp 
                ON stock_data(timestamp);
            """))
            conn.commit()

        logger.info("Veritabanı başarıyla sıfırlandı")
        return True

    except Exception as e:
        logger.error(f"Veritabanı sıfırlama hatası: {str(e)}")
        return False


def main() -> None:
    """Ana uygulama fonksiyonu."""
    engine = get_db_connection()
    if not engine:
        logger.error("Veritabanına bağlanılamadı!")
        return

    if reset_database(engine):
        logger.info("Veritabanı sıfırlama işlemi başarılı")
    else:
        logger.error("Veritabanı sıfırlama işlemi başarısız!")


if __name__ == "__main__":
    main()