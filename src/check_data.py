"""Module for checking data quality in the database."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from sqlalchemy import text

from src.database.postgres_manager import PostgresManager

# Log configuration
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_data_stats(db: PostgresManager) -> Dict[str, float]:
    """
    Calculate statistics of data in the database.

    Args:
        db: PostgresManager instance

    Returns:
        Dict[str, float]: Statistics values
    """
    try:
        session = db._get_session()
        try:
            result = session.execute(
                text(
                    """
                SELECT
                    COUNT(*) as total_records,
                    COUNT(DISTINCT symbol) as unique_symbols,
                    AVG(price) as avg_price,
                    MIN(price) as min_price,
                    MAX(price) as max_price,
                    AVG(volume) as avg_volume,
                    MIN(collected_at) as first_record,
                    MAX(collected_at) as last_record
                FROM stock_data;
            """
                )
            )
            stats = result.mappings().first()

            if not stats:
                return {}

            return dict(stats)
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Statistics calculation error: {str(e)}")
        return {}


def check_data_distribution(db: PostgresManager) -> None:
    """Check data distribution for each symbol in last 5 minutes."""
    try:
        session = db._get_session()
        try:
            cutoff_time = datetime.now() - timedelta(minutes=5)
            result = session.execute(
                text(
                    """
                WITH time_diffs AS (
                    SELECT
                        symbol,
                        collected_at,
                        EXTRACT(EPOCH FROM
                            collected_at - LAG(collected_at)
                            OVER (PARTITION BY symbol ORDER BY collected_at)
                        ) as interval_seconds
                    FROM stock_data
                    WHERE collected_at > :cutoff
                )
                SELECT
                    symbol,
                    COUNT(*) as record_count,
                    AVG(interval_seconds) as avg_interval,
                    MIN(interval_seconds) as min_interval,
                    MAX(interval_seconds) as max_interval
                FROM time_diffs
                WHERE interval_seconds IS NOT NULL
                AND interval_seconds > 0
                GROUP BY symbol
                ORDER BY symbol;
            """
                ),
                {"cutoff": cutoff_time},
            )

            logger.info("\nData Distribution (Last 5 minutes):")
            for row in result.mappings():
                logger.info(
                    f"Symbol: {row['symbol']}, "
                    f"Records: {row['record_count']}, "
                    f"Avg Interval: {row['avg_interval']:.1f}s, "
                    f"Min: {row['min_interval']:.1f}s, "
                    f"Max: {row['max_interval']:.1f}s"
                )
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Data distribution check error: {str(e)}")


def check_data_quality(db: PostgresManager) -> List[str]:
    """
    Perform data quality checks.

    Args:
        db: PostgresManager instance

    Returns:
        List[str]: List of detected issues
    """
    issues = []
    try:
        session = db._get_session()
        try:
            # Null value check
            null_check = session.execute(
                text(
                    """
                SELECT COUNT(*)
                FROM stock_data
                WHERE price IS NULL
                OR volume IS NULL
                OR symbol IS NULL;
            """
                )
            )
            null_count = null_check.scalar()
            if null_count > 0:
                issues.append(f"Null count: {null_count}")

            # Negative price check
            negative_price = session.execute(
                text(
                    """
                SELECT COUNT(*)
                FROM stock_data
                WHERE price < 0;
            """
                )
            )
            if negative_price.scalar() > 0:
                issues.append("Negative price values found!")

            # Data frequency check
            frequency_check = session.execute(
                text(
                    """
                WITH time_diffs AS (
                    SELECT
                        symbol,
                        collected_at,
                        EXTRACT(EPOCH FROM
                            collected_at - LAG(collected_at)
                            OVER (PARTITION BY symbol ORDER BY collected_at)
                        ) as interval_seconds
                    FROM stock_data
                )
                SELECT AVG(interval_seconds)
                FROM time_diffs
                WHERE interval_seconds IS NOT NULL
                AND interval_seconds > 0;
            """
                )
            )
            avg_seconds = frequency_check.scalar() or 0
            if avg_seconds > 5:  # If there is more than 5 seconds gap
                issues.append(
                    f"Average data collection frequency is too low: "
                    f"{avg_seconds:.1f} seconds"
                )
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Data quality check error: {str(e)}")
        issues.append(f"Error during check: {str(e)}")

    return issues


def get_missing_periods(
    db: PostgresManager, threshold_seconds: int = 5
) -> List[Tuple[str, datetime, datetime]]:
    """
    Find missing time periods.

    Args:
        db: PostgresManager instance
        threshold_seconds: Acceptable maximum gap (seconds)

    Returns:
        List[Tuple[str, datetime, datetime]]:
            Symbol and missing data periods list
    """
    missing_periods = []
    try:
        session = db._get_session()
        try:
            # Sorted time stamps for each symbol
            symbols = session.execute(
                text("SELECT DISTINCT symbol FROM stock_data;")
            ).scalars()

            for symbol in symbols:
                result = session.execute(
                    text(
                        """
                    SELECT
                        collected_at,
                        LEAD(collected_at) OVER (
                            ORDER BY collected_at
                        ) as next_time
                    FROM stock_data
                    WHERE symbol = :symbol
                    ORDER BY collected_at;
                """
                    ),
                    {"symbol": symbol},
                )

                for row in result:
                    if row.next_time:
                        gap = (row.next_time - row.collected_at).total_seconds()
                        if gap > threshold_seconds:
                            missing_periods.append(
                                (symbol, row.collected_at, row.next_time)
                            )
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Missing period check error: {str(e)}")

    return missing_periods


def main() -> None:
    """Main application function."""
    db = PostgresManager()

    # Get statistics
    stats = get_data_stats(db)
    if stats:
        logger.info("\nData Statistics:")
        for key, value in stats.items():
            logger.info(f"{key}: {value}")

    # Check data distribution
    check_data_distribution(db)

    # Data quality check
    issues = check_data_quality(db)
    if issues:
        logger.warning("\nDetected Issues:")
        for issue in issues:
            logger.warning(f"- {issue}")
    else:
        logger.info("\nData quality checks successful!")

    # Check missing periods
    missing_periods = get_missing_periods(db)
    if missing_periods:
        logger.warning("\nMissing Data Periods:")
        for symbol, start, end in missing_periods:
            logger.warning(f"Symbol: {symbol}, " f"Start: {start}, " f"End: {end}")
    else:
        logger.info("\nNo missing data periods found!")


if __name__ == "__main__":
    main()
