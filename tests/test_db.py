"""Veritabanı işlemleri için test modülü."""

from datetime import datetime
from typing import Dict, List

import pytest
from sqlalchemy.orm import Session

from src.database.postgres_manager import PostgresManager, StockData


def test_db_connection(db_manager: PostgresManager) -> None:
    """
    Veritabanı bağlantı testi.

    Args:
        db_manager: PostgresManager fixture'ı
    """
    assert db_manager.engine is not None, "Engine oluşturulamadı"
    assert db_manager.Session is not None, "Session oluşturulamadı"

    # Bağlantıyı test et
    with db_manager.engine.connect() as conn:
        result = conn.execute("SELECT 1")
        assert result.scalar() == 1, "Veritabanı bağlantısı başarısız"


def test_insert_stock_data(
    db_manager: PostgresManager,
    sample_stock_data: Dict,
    clean_db: None
) -> None:
    """
    Veri ekleme testi.

    Args:
        db_manager: PostgresManager fixture'ı
        sample_stock_data: Örnek veri fixture'ı
        clean_db: Veritabanı temizleme fixture'ı
    """
    # Veriyi ekle
    result = db_manager.insert_stock_data(sample_stock_data)
    assert result is not None, "Veri eklenemedi"
    
    # Eklenen veriyi kontrol et
    session = db_manager.Session()
    try:
        record = session.query(StockData)\
            .filter_by(symbol=sample_stock_data['symbol'])\
            .first()
        
        assert record is not None, "Kayıt bulunamadı"
        assert record.symbol == sample_stock_data['symbol'], "Sembol eşleşmiyor"
        assert record.price == sample_stock_data['price'], "Fiyat eşleşmiyor"
        assert record.volume == sample_stock_data['volume'], "Hacim eşleşmiyor"
    finally:
        session.close()


def test_get_latest_records(
    db_manager: PostgresManager,
    sample_stock_data: Dict,
    clean_db: None
) -> None:
    """
    Son kayıtları getirme testi.

    Args:
        db_manager: PostgresManager fixture'ı
        sample_stock_data: Örnek veri fixture'ı
        clean_db: Veritabanı temizleme fixture'ı
    """
    # Test verilerini ekle
    for i in range(5):
        data = sample_stock_data.copy()
        data['price'] = float(100 + i)  # Her kayıt için farklı fiyat
        data['timestamp'] = f"2024-02-20 12:{i:02d}:00"
        data['collected_at'] = f"2024-02-20T12:{i:02d}:00"
        result = db_manager.insert_stock_data(data)
        assert result is not None, f"Veri eklenemedi: {data}"
    
    # Son 3 kaydı al
    records = db_manager.get_latest_records(limit=3)
    
    # Sonuçları kontrol et
    assert len(records) == 3, "Yanlış sayıda kayıt döndü"
    assert records[0].price > records[1].price, (
        f"İlk fiyat ({records[0].price}) ikinci fiyattan "
        f"({records[1].price}) büyük olmalı"
    )
    assert records[1].price > records[2].price, (
        f"İkinci fiyat ({records[1].price}) üçüncü fiyattan "
        f"({records[2].price}) büyük olmalı"
    )


def test_bulk_insert(
    db_manager: PostgresManager,
    multiple_stock_data: List[Dict],
    clean_db: None
) -> None:
    """
    Toplu veri ekleme testi.

    Args:
        db_manager: PostgresManager fixture'ı
        multiple_stock_data: Çoklu veri fixture'ı
        clean_db: Veritabanı temizleme fixture'ı
    """
    # Verileri ekle
    for data in multiple_stock_data:
        result = db_manager.insert_stock_data(data)
        assert result is not None, f"Veri eklenemedi: {data}"
    
    # Eklenen verileri kontrol et
    session = db_manager.Session()
    try:
        for data in multiple_stock_data:
            record = session.query(StockData)\
                .filter_by(symbol=data['symbol'])\
                .first()
            
            assert record is not None, f"Kayıt bulunamadı: {data['symbol']}"
            assert record.price == data['price'], (
                f"Fiyat eşleşmiyor: {data['symbol']}"
            )
    finally:
        session.close()


def test_error_handling(
    db_manager: PostgresManager,
    clean_db: None
) -> None:
    """
    Hata yönetimi testi.

    Args:
        db_manager: PostgresManager fixture'ı
        clean_db: Veritabanı temizleme fixture'ı
    """
    # Geçersiz veri
    invalid_data = {
        'symbol': 'TEST' * 10,  # Çok uzun sembol
        'price': 'invalid',     # Geçersiz fiyat tipi
        'volume': None,         # Boş hacim
        'timestamp': 'invalid', # Geçersiz zaman damgası
        'collected_at': 'now'   # Geçersiz toplama zamanı
    }
    
    # Eklemeyi dene
    result = db_manager.insert_stock_data(invalid_data)
    assert result is None, "Geçersiz veri kabul edildi"
    
    # Veritabanında kayıt olmamalı
    session = db_manager.Session()
    try:
        count = session.query(StockData).count()
        assert count == 0, "Geçersiz veri kaydedildi"
    finally:
        session.close()


if __name__ == "__main__":
    pytest.main(["-v", __file__])