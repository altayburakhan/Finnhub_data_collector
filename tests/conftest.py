"""Module for configuration of test fixtures"""

import os
from datetime import datetime
from typing import Dict, Generator, List

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.database.postgres_manager import Base, PostgresManager, StockData

load_dotenv()


@pytest.fixture(scope="session")
def db_url() -> str:
    """
    Create test database URL.

    Returns:
        str: Database connection URL
    """
    return (
        f"postgresql://{os.getenv('POSTGRES_USER')}:"
        f"{os.getenv('POSTGRES_PASSWORD')}@"
        f"{os.getenv('POSTGRES_HOST')}:"
        f"{os.getenv('POSTGRES_PORT')}/"
        f"{os.getenv('POSTGRES_DB')}"
    )


@pytest.fixture(scope="session")
def engine():
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "postgres")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    engine = create_engine(DATABASE_URL)
    
    # Create tables before running tests
    Base.metadata.create_all(engine)
    
    return engine


@pytest.fixture(scope="session")
def tables(engine: Engine) -> Generator[None, None, None]:
    """
    Create test tables and clean them up after tests.

    Args:
        engine: SQLAlchemy engine object

    Yields:
        None: No value returned
    """
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="session")
def db_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    # Clean up after tests
    session.close()


@pytest.fixture(scope="session", autouse=True)
def load_env() -> None:
    """Load environment variables before running tests."""
    load_dotenv()
    # Test ortamı için varsayılan değerleri ayarla
    os.environ.setdefault("POSTGRES_HOST", "localhost")
    os.environ.setdefault("POSTGRES_PORT", "5432")
    os.environ.setdefault("POSTGRES_DB", "postgres")
    os.environ.setdefault("POSTGRES_USER", "postgres")
    os.environ.setdefault("POSTGRES_PASSWORD", "postgres")


@pytest.fixture
def db_manager() -> Generator[PostgresManager, None, None]:
    """Create a database manager for testing."""
    manager = PostgresManager()
    yield manager


@pytest.fixture(scope="session")
def sample_stock_data() -> Dict:
    """
    Create sample stock data for testing.

    Returns:
        Dict: Sample data for testing
    """
    now = datetime.now()
    return {
        "symbol": "AAPL",
        "price": 150.0,
        "volume": 1000000.0,
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "collected_at": now.isoformat(),
    }


@pytest.fixture(scope="session")
def multiple_stock_data() -> List[Dict]:
    """
    Create multiple sample stock data for testing.

    Returns:
        List[Dict]: Sample data list for testing
    """
    now = datetime.now()
    return [
        {
            "symbol": symbol,
            "price": 150.0,
            "volume": 1000000.0,
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "collected_at": now.isoformat(),
        }
        for symbol in ["AAPL", "MSFT", "GOOGL"]
    ]


@pytest.fixture(autouse=True)
def clean_db(db_session):
    try:
        # Clean existing data
        db_session.execute(text("TRUNCATE TABLE stock_data RESTART IDENTITY CASCADE"))
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        raise e
