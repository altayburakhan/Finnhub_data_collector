"""Test module for database operations"""

from datetime import datetime
from typing import Any, Dict, List, Union, cast

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from src.database.postgres_manager import PostgresManager, StockData, StockDataDict

InvalidDataDict = Dict[str, Union[str, float, None]]


def test_db_connection(db_manager: PostgresManager) -> None:
    """
    Test for database connection.

    Args:
        db_manager: PostgresManager fixture
    """
    assert db_manager.engine is not None, "Engine could not be created"
    
    # Test connection
    with db_manager.engine.connect() as conn:
        result = conn.execute("SELECT 1").scalar()
        assert result == 1, "Database connection failed"


def test_insert_stock_data(db_manager: PostgresManager) -> None:
    """
    Test for data insertion.

    Args:
        db_manager: PostgresManager fixture
    """
    # Create test data
    test_data = {
        "symbol": "TEST",
        "price": 100.0,
        "volume": 1000.0,
        "timestamp": datetime.now(),
        "collected_at": datetime.now()
    }
    
    # Insert data
    session = db_manager.Session()
    try:
        result = db_manager.insert_stock_data(test_data)
        assert result is True, "Data insertion failed"
        
        # Verify insertion
        inserted_data = session.query(StockData).filter_by(symbol="TEST").first()
        assert inserted_data is not None
        assert inserted_data.symbol == "TEST"
        assert inserted_data.price == 100.0
    finally:
        session.close()


def test_get_latest_records(
    db_manager: PostgresManager,
    sample_stock_data: StockDataDict,
) -> None:
    """
    Test for getting latest records.

    Args:
        db_manager: PostgresManager fixture
        sample_stock_data: Sample data fixture
    """
    for i in range(5):
        data = sample_stock_data.copy()
        data["price"] = float(100 + i)
        data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data["collected_at"] = datetime.now().isoformat()
        result = db_manager.insert_stock_data(data)
        assert result is not None, f"Data could not be inserted: {data}"

    records = db_manager.get_latest_records(limit=3)

    assert len(records) == 3, "Wrong number of records returned"
    assert records[0].price > records[1].price, (
        f"First price ({records[0].price}) should be greater than "
        f"second price ({records[1].price})"
    )
    assert records[1].price > records[2].price, (
        f"Second price ({records[1].price}) should be greater than "
        f"third price ({records[2].price})"
    )


def test_bulk_insert(
    db_manager: PostgresManager,
    multiple_stock_data: List[StockDataDict],
) -> None:
    """
    Test for bulk data insertion.

    Args:
        db_manager: PostgresManager fixture
        multiple_stock_data: Multiple data fixture
    """
    for data in multiple_stock_data:
        result = db_manager.insert_stock_data(data)
        assert result is not None, f"Data could not be inserted: {data}"

    session_factory = cast(sessionmaker, db_manager.Session)
    session = session_factory()
    try:
        for data in multiple_stock_data:
            record = session.query(StockData).filter_by(symbol=data["symbol"]).first()

            assert record is not None, f"Record not found: {data['symbol']}"
            assert (
                record.price == data["price"]
            ), f"Price does not match: {data['symbol']}"
    finally:
        session.close()


def test_error_handling(db_manager: PostgresManager) -> None:
    """
    Test for error handling.

    Args:
        db_manager: PostgresManager fixture
    """
    invalid_data: StockDataDict = {
        "symbol": "TEST" * 10,
        "price": "invalid",  # type: ignore
        "volume": None,  # type: ignore
        "timestamp": "invalid",
        "collected_at": "now",
    }

    result = db_manager.insert_stock_data(invalid_data)
    assert result is None, "Invalid data accepted"

    session_factory = cast(sessionmaker, db_manager.Session)
    session = session_factory()
    try:
        count = session.query(StockData).count()
        assert count == 0, "Invalid data was inserted"
    finally:
        session.close()


if __name__ == "__main__":
    pytest.main(["-v", __file__])
