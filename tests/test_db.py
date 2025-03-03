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
    
    # Test connection using text()
    with db_manager.engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
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


def test_get_latest_records(db_manager: PostgresManager) -> None:
    """
    Test for getting latest records.

    Args:
        db_manager: PostgresManager fixture
    """
    # Insert some test data first
    test_data = [
        {
            "symbol": "TEST1",
            "price": 100.0,
            "volume": 1000.0,
            "timestamp": datetime.now(),
            "collected_at": datetime.now()
        },
        {
            "symbol": "TEST2",
            "price": 200.0,
            "volume": 2000.0,
            "timestamp": datetime.now(),
            "collected_at": datetime.now()
        }
    ]
    
    for data in test_data:
        db_manager.insert_stock_data(data)
    
    # Test getting latest records
    records = db_manager.get_latest_records(limit=3)
    assert len(records) > 0, "No records returned"
    assert isinstance(records[0], dict), "Record should be a dictionary"
    assert "symbol" in records[0], "Record should have symbol field"


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
    # Test with invalid price
    invalid_data = {
        "symbol": "TEST" * 10,  # Too long symbol
        "price": "invalid",
        "volume": 1000.0,
        "timestamp": datetime.now(),
        "collected_at": datetime.now()
    }
    
    result = db_manager.insert_stock_data(invalid_data)
    assert result is None, "Invalid data should be rejected"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
