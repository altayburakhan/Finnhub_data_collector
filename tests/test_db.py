"""Test module for database operations"""

from datetime import datetime
from typing import Any, Dict, List, Union, cast

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from src.database.postgres_manager import PostgresManager, StockData

StockDataDict = Dict[str, Union[str, float, datetime]]
InvalidDataDict = Dict[str, Union[str, float, None]]


def test_db_connection(db_manager: PostgresManager) -> None:
    """
    Test for database connection.

    Args:
        db_manager: PostgresManager fixture
    """
    assert db_manager.engine is not None, "Engine could not be created"
    assert isinstance(db_manager.Session, sessionmaker), "Session could not be created"

    # Test connection
    with db_manager.engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1, "Database connection failed"


def test_insert_stock_data(
    db_manager: PostgresManager,
    sample_stock_data: StockDataDict,
) -> None:
    """
    Test for data insertion.

    Args:
        db_manager: PostgresManager fixture
        sample_stock_data: Sample data fixture
    """
    # Insert data
    result = db_manager.insert_stock_data(sample_stock_data)
    assert result is not None, "Data could not be inserted"

    # Check inserted data
    session_factory = cast(sessionmaker, db_manager.Session)
    session = session_factory()
    try:
        record = (
            session.query(StockData)
            .filter_by(symbol=sample_stock_data["symbol"])
            .first()
        )

        assert record is not None, "Record not found"
        assert record.symbol == sample_stock_data["symbol"], "Symbol does not match"
        assert record.price == sample_stock_data["price"], "Price does not match"
        assert record.volume == sample_stock_data["volume"], "Volume does not match"
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
    # Insert test data
    for i in range(5):
        data = sample_stock_data.copy()
        data["price"] = float(100 + i)  # Different price for each record
        data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data["collected_at"] = datetime.now().isoformat()
        result = db_manager.insert_stock_data(data)
        assert result is not None, f"Data could not be inserted: {data}"

    # Get last 3 records
    records = db_manager.get_latest_records(limit=3)

    # Check results
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
    # Insert data
    for data in multiple_stock_data:
        result = db_manager.insert_stock_data(data)
        assert result is not None, f"Data could not be inserted: {data}"

    # Check inserted data
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
    # Invalid data with explicit type casting
    invalid_data: InvalidDataDict = {
        "symbol": "TEST" * 10,  # Too long symbol
        "price": "invalid",  # Invalid price type
        "volume": None,  # Empty volume
        "timestamp": "invalid",  # Invalid timestamp
        "collected_at": "now",  # Invalid collection time
    }

    # Try to insert - using Any to bypass type checking for invalid data test
    result = db_manager.insert_stock_data(invalid_data)  # type: ignore
    assert result is None, "Invalid data accepted"

    # No record should be in database
    session_factory = cast(sessionmaker, db_manager.Session)
    session = session_factory()
    try:
        count = session.query(StockData).count()
        assert count == 0, "Invalid data was inserted"
    finally:
        session.close()


if __name__ == "__main__":
    pytest.main(["-v", __file__])
