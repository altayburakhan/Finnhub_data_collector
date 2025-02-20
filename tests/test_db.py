import pytest
from datetime import datetime
from src.database.postgres_manager import StockData

def test_db_connection(db_manager):
    """Veritabanı bağlantı testi"""
    assert db_manager.engine is not None
    assert db_manager.Session is not None

def test_insert_stock_data(db_manager, sample_stock_data):
    """Veri ekleme testi"""
    try:
        # Veriyi ekle
        result = db_manager.insert_stock_data(sample_stock_data)
        
        # Kontroller
        assert result is not None
        assert isinstance(result, StockData)
        assert result.symbol == sample_stock_data['symbol']
        assert result.price == sample_stock_data['price']
        assert result.volume == sample_stock_data['volume']
    except Exception as e:
        pytest.fail(f"Test başarısız: {str(e)}")

def test_insert_invalid_data(db_manager):
    """Geçersiz veri ekleme testi"""
    invalid_data = {
        'symbol': 'TEST',
        # price eksik
        'volume': 1000,
        'timestamp': '2024-02-20 12:00:00',
        'collected_at': '2024-02-20T12:00:00'
    }
    
    result = db_manager.insert_stock_data(invalid_data)
    assert result is None

def test_get_latest_records(db_manager, sample_stock_data):
    """Son kayıtları getirme testi"""
    # Test verilerini ekle
    for i in range(5):
        data = sample_stock_data.copy()
        data['price'] = 100.0 + i  # Her kayıt için farklı fiyat
        data['timestamp'] = f"2024-02-20 12:{i:02d}:00"  # Farklı zaman damgaları
        data['collected_at'] = f"2024-02-20T12:{i:02d}:00"
        db_manager.insert_stock_data(data)
    
    # Son 3 kaydı al
    records = db_manager.get_latest_records(limit=3)
    
    assert len(records) == 3
    # Fiyatları kontrol et (son eklenen en yüksek fiyata sahip olmalı)
    assert records[0].price > records[1].price
    assert records[1].price > records[2].price