"""Module for configuration of test fixtures"""

import os
from datetime import datetime
from typing import Dict, Generator, List

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.database.postgres_manager import Base, PostgresManager, StockData

# Load .env file for test database configuration
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
def engine(db_url: str) -> Engine:
    """
    Create test database engine.

    Args:
        db_url: Database connection URL

    Returns:
        Engine: SQLAlchemy engine object
    """
    return create_engine(db_url)


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


@pytest.fixture
def db_session(engine: Engine, tables: None) -> Generator[Session, None, None]:
    """
    Create a database session for testing.

    Args:
        engine: SQLAlchemy engine object
        tables: Test tables (fixture)

    Yields:
        Session: SQLAlchemy session object
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
    Create a PostgresManager instance for testing.

    Args:
        engine: SQLAlchemy engine object
        tables: Test tables (fixture)

    Returns:
        PostgresManager: Database manager instance
    """
    manager = PostgresManager()
    manager.engine = engine
    manager._session_factory = sessionmaker(bind=engine)
    manager.Session = manager._session_factory
    return manager


@pytest.fixture
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


@pytest.fixture
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
            "price": 150.0,  # Same price for all stocks in test
            "volume": 1000000.0,
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "collected_at": now.isoformat(),
        }
        for symbol in ["AAPL", "MSFT", "GOOGL"]
    ]


@pytest.fixture(autouse=True)
def clean_db(db_session: Session) -> None:
    """
    Clean the test database before each test.

    Args:
        db_session: SQLAlchemy session object
    """
    try:
        db_session.query(StockData).delete()
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        raise e
