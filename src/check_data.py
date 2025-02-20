"""Veritabanındaki verilerin kalite kontrolü için modül."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine.base import Engine

from src.database.postgres_manager import PostgresManager

# Log yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_data_stats(db: PostgresManager) -> Dict[str, float]:
    """
    Veritabanındaki verilerin istatistiklerini hesapla.

    Args:
        db: PostgresManager instance

    Returns:
        Dict[str, float]: İstatistik değerleri
    """
    try:
        with db.Session() as session:
            result = session.execute(text("""
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
            """))
            stats = result.mappings().first()
            
            if not stats:
                return {}
            
            return dict(stats)
    except Exception as e:
        logger.error(f"İstatistik hesaplama hatası: {str(e)}")
        return {}


def check_data_quality(db: PostgresManager) -> List[str]:
    """
    Veri kalitesi kontrollerini gerçekleştir.

    Args:
        db: PostgresManager instance

    Returns:
        List[str]: Tespit edilen sorunların listesi
    """
    issues = []
    try:
        with db.Session() as session:
            # Boş değer kontrolü
            null_check = session.execute(text("""
                SELECT COUNT(*) 
                FROM stock_data 
                WHERE price IS NULL 
                OR volume IS NULL 
                OR symbol IS NULL;
            """))
            null_count = null_check.scalar()
            if null_count > 0:
                issues.append(f"Boş değer sayısı: {null_count}")

            # Negatif fiyat kontrolü
            negative_price = session.execute(text("""
                SELECT COUNT(*) 
                FROM stock_data 
                WHERE price < 0;
            """))
            if negative_price.scalar() > 0:
                issues.append("Negatif fiyat değerleri mevcut!")

            # Veri sıklığı kontrolü
            frequency_check = session.execute(text("""
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
            """))
            avg_seconds = frequency_check.scalar() or 0
            if avg_seconds > 5:  # 3 saniyeden fazla boşluk varsa
                issues.append(
                    f"Ortalama veri toplama sıklığı çok düşük: "
                    f"{avg_seconds:.1f} saniye"
                )

    except Exception as e:
        logger.error(f"Veri kalitesi kontrol hatası: {str(e)}")
        issues.append(f"Kontrol sırasında hata: {str(e)}")

    return issues


def get_missing_periods(
    db: PostgresManager,
    threshold_seconds: int = 5
) -> List[Tuple[str, datetime, datetime]]:
    """
    Veri eksik olan zaman aralıklarını bul.

    Args:
        db: PostgresManager instance
        threshold_seconds: Kabul edilebilir maksimum boşluk (saniye)

    Returns:
        List[Tuple[str, datetime, datetime]]: 
            Sembol ve eksik veri aralıkları listesi
    """
    missing_periods = []
    try:
        with db.Session() as session:
            # Her sembol için sıralı zaman damgaları
            symbols = session.execute(text(
                "SELECT DISTINCT symbol FROM stock_data;"
            )).scalars()

            for symbol in symbols:
                result = session.execute(text("""
                    SELECT 
                        collected_at,
                        LEAD(collected_at) OVER (
                            ORDER BY collected_at
                        ) as next_time
                    FROM stock_data
                    WHERE symbol = :symbol
                    ORDER BY collected_at;
                """), {"symbol": symbol})

                for row in result:
                    if row.next_time:
                        gap = (row.next_time - row.collected_at).total_seconds()
                        if gap > threshold_seconds:
                            missing_periods.append(
                                (symbol, row.collected_at, row.next_time)
                            )

    except Exception as e:
        logger.error(f"Eksik period kontrolü hatası: {str(e)}")

    return missing_periods


def main() -> None:
    """Ana uygulama fonksiyonu."""
    db = PostgresManager()

    # İstatistikleri al
    stats = get_data_stats(db)
    if stats:
        logger.info("\nVeri İstatistikleri:")
        for key, value in stats.items():
            logger.info(f"{key}: {value}")

    # Veri kalitesi kontrolü
    issues = check_data_quality(db)
    if issues:
        logger.warning("\nTespit Edilen Sorunlar:")
        for issue in issues:
            logger.warning(f"- {issue}")
    else:
        logger.info("\nVeri kalitesi kontrolleri başarılı!")

    # Eksik periyodları kontrol et
    missing_periods = get_missing_periods(db)
    if missing_periods:
        logger.warning("\nEksik Veri Periyotları:")
        for symbol, start, end in missing_periods:
            logger.warning(
                f"Sembol: {symbol}, "
                f"Başlangıç: {start}, "
                f"Bitiş: {end}"
            )
    else:
        logger.info("\nEksik veri periyodu bulunamadı!")


if __name__ == "__main__":
    main()