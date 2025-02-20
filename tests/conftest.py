"""Test fixture'ları için yapılandırma modülü."""

import os
from datetime import datetime
from typing import Dict, Generator, List

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.database.postgres_manager import Base, PostgresManager, StockData

# Test veritabanı yapılandırması için .env dosyasını yükle
load_dotenv()


@pytest.fixture(scope="session")
def db_url() -> str:
    """
    Test veritabanı URL'sini oluştur.

    Returns:
        str: Veritabanı bağlantı URL'si
    """
    return (
        f"postgresql://{os.getenv('POSTGRES_USER')}:"
        f"{os.getenv('POSTGRES_PASSWORD')}@"
        f"{os.getenv('POSTGRES_HOST')}:"
        f"{os.getenv('POSTGRES_PORT')}/"
        f"{os.getenv('POSTGRES_DB')}_test"  # Test için ayrı veritabanı
    )


@pytest.fixture(scope="session")
def engine(db_url: str) -> Engine:
    """
    Test veritabanı engine'ini oluştur.

    Args:
        db_url: Veritabanı bağlantı URL'si

    Returns:
        Engine: SQLAlchemy engine objesi
    """
    return create_engine(db_url)


@pytest.fixture(scope="session")
def tables(engine: Engine) -> Generator[None, None, None]:
    """
    Test tablolarını oluştur ve test sonunda temizle.

    Args:
        engine: SQLAlchemy engine objesi

    Yields:
        None: Bir değer döndürmez
    """
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(
    engine: Engine, tables: None
) -> Generator[Session, None, None]:
    """
    Test için veritabanı oturumu oluştur.

    Args:
        engine: SQLAlchemy engine objesi
        tables: Test tabloları (fixture)

    Yields:
        Session: SQLAlchemy session objesi
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def db_manager(engine: Engine, tables: None) -> PostgresManager:
    """
    Test için PostgresManager instance'ı oluştur.

    Args:
        engine: SQLAlchemy engine objesi
        tables: Test tabloları (fixture)

    Returns:
        PostgresManager: Veritabanı yönetici sınıfı instance'ı
    """
    manager = PostgresManager()
    manager.engine = engine
    manager.Session = sessionmaker(bind=engine)
    return manager


@pytest.fixture
def sample_stock_data() -> Dict:
    """
    Örnek hisse senedi verisi oluştur.

    Returns:
        Dict: Test için örnek veri
    """
    return {
        'symbol': 'AAPL',
        'price': 150.0,
        'volume': 1000000.0,
        'timestamp': '2024-02-20 12:00:00',
        'collected_at': datetime.now().isoformat()
    }


@pytest.fixture
def multiple_stock_data() -> List[Dict]:
    """
    Birden fazla örnek hisse senedi verisi oluştur.

    Returns:
        List[Dict]: Test için örnek veri listesi
    """
    base_time = datetime(2024, 2, 20, 12, 0, 0)
    return [
        {
            'symbol': symbol,
            'price': 100.0 + i,
            'volume': 1000000.0 + (i * 1000),
            'timestamp': (base_time).strftime('%Y-%m-%d %H:%M:%S'),
            'collected_at': (base_time).isoformat()
        }
        for i, symbol in enumerate(['AAPL', 'MSFT', 'GOOGL'])
    ]


@pytest.fixture
def clean_db(db_session: Session) -> None:
    """
    Test veritabanını temizle.

    Args:
        db_session: SQLAlchemy session objesi
    """
    db_session.query(StockData).delete()
    db_session.commit()