"""Veritabanı bağlantı testi için modül."""

import logging
import os
from typing import Optional, Tuple

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


def test_connection(engine: Engine) -> Tuple[bool, str]:
    """
    Veritabanı bağlantısını test et.

    Args:
        engine: SQLAlchemy engine objesi

    Returns:
        Tuple[bool, str]: (Başarılı mı, Mesaj)
    """
    try:
        # Bağlantıyı test et
        with engine.connect() as conn:
            # PostgreSQL versiyonunu al
            result = conn.execute(text("SELECT version();"))
            version = result.scalar()

            # Tablo sayısını kontrol et
            result = conn.execute(text("""
                SELECT count(*)
                FROM information_schema.tables
                WHERE table_schema = 'public';
            """))
            table_count = result.scalar()

        return True, (
            f"Bağlantı başarılı!\n"
            f"PostgreSQL Versiyon: {version}\n"
            f"Tablo Sayısı: {table_count}"
        )

    except Exception as e:
        error_msg = f"Bağlantı hatası: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def check_table_exists(engine: Engine, table_name: str) -> bool:
    """
    Belirtilen tablonun var olup olmadığını kontrol et.

    Args:
        engine: SQLAlchemy engine objesi
        table_name: Kontrol edilecek tablo adı

    Returns:
        bool: Tablo varsa True, yoksa False
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = :table_name
                );
            """), {"table_name": table_name})
            return result.scalar()
    except Exception as e:
        logger.error(f"Tablo kontrol hatası: {str(e)}")
        return False


def main() -> None:
    """Ana uygulama fonksiyonu."""
    # Veritabanı bağlantısını al
    engine = get_db_connection()
    if not engine:
        logger.error("Veritabanı bağlantısı oluşturulamadı!")
        return

    # Bağlantıyı test et
    success, message = test_connection(engine)
    if success:
        logger.info(message)
        
        # stock_data tablosunu kontrol et
        if check_table_exists(engine, "stock_data"):
            logger.info("stock_data tablosu mevcut")
        else:
            logger.warning("stock_data tablosu bulunamadı!")
    else:
        logger.error(message)


if __name__ == "__main__":
    main()