"""Module for checking data quality in the database."""

import logging
from datetime import datetime
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
        logger.error(f"İstatistik hesaplama hatası: {str(e)}")
        return {}


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
                WITH time_diff AS (
                    SELECT
                        symbol,
                        collected_at,
                        EXTRACT(EPOCH FROM
                            collected_at - LAG(collected_at)
                            OVER (PARTITION BY symbol ORDER BY collected_at)
                        ) as diff_seconds
                    FROM stock_data
                )
                SELECT AVG(diff_seconds)
                FROM time_diff
                WHERE diff_seconds IS NOT NULL;
            """
                )
            )
            avg_seconds = frequency_check.scalar() or 0
            if avg_seconds > 5:  # If there is more than 3 seconds gap
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
