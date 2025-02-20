"""Finnhub API testleri için modül."""

import os
from datetime import datetime
from typing import Dict
from unittest.mock import MagicMock, patch

import pytest
import requests
from dotenv import load_dotenv

from main import FinnhubAPI
from src.database.postgres_manager import StockData

# Test yapılandırması
load_dotenv()
API_KEY = os.getenv("FINNHUB_API_KEY")


@pytest.fixture
def mock_response() -> MagicMock:
    """
    Mock API yanıtı oluştur.

    Returns:
        MagicMock: Sahte API yanıtı
    """
    mock = MagicMock()
    mock.json.return_value = {"c": 150.5, "t": 1000000}
    mock.status_code = 200
    return mock


@pytest.fixture
def api_instance(db_manager) -> FinnhubAPI:
    """
    Test için FinnhubAPI instance'ı oluştur.

    Args:
        db_manager: Veritabanı yönetici fixture'ı

    Returns:
        FinnhubAPI: API sınıfı instance'ı
    """
    api = FinnhubAPI()
    api.db_manager = db_manager
    return api


def test_api_initialization() -> None:
    """API başlatma testleri."""
    api = FinnhubAPI()
    
    assert api.api_key == API_KEY, "API anahtarı yüklenemedi"
    assert api.base_url == "https://finnhub.io/api/v1", "Base URL hatalı"
    assert len(api.symbols) > 0, "Sembol listesi boş"
    assert api.db_manager is not None, "Veritabanı yöneticisi oluşturulamadı"


@patch("requests.get")
def test_collect_symbol_data(
    mock_get: MagicMock,
    api_instance: FinnhubAPI,
    mock_response: MagicMock
) -> None:
    """
    Veri toplama fonksiyonu testi.

    Args:
        mock_get: Requests.get mock'u
        api_instance: FinnhubAPI instance'ı
        mock_response: Mock API yanıtı
    """
    # Mock ayarları
    mock_get.return_value = mock_response
    
    # Test verisi
    test_symbol = "AAPL"
    
    # Fonksiyonu çağır
    api_instance.collect_symbol_data(test_symbol)
    
    # API çağrısını kontrol et
    mock_get.assert_called_once()
    call_args = mock_get.call_args[1]
    assert "symbol" in call_args["params"], "Symbol parametresi eksik"
    assert "token" in call_args["params"], "Token parametresi eksik"
    
    # Veritabanına yazma işlemini kontrol et
    session = api_instance.db_manager.Session()
    latest_record = session.query(StockData)\
        .filter_by(symbol=test_symbol)\
        .order_by(StockData.collected_at.desc())\
        .first()
    
    assert latest_record is not None, "Veri kaydedilemedi"
    assert latest_record.symbol == test_symbol, "Yanlış sembol kaydedildi"
    assert latest_record.price == 150.5, "Yanlış fiyat kaydedildi"
    
    session.close()


@patch("requests.get")
def test_api_error_handling(
    mock_get: MagicMock,
    api_instance: FinnhubAPI
) -> None:
    """
    API hata yönetimi testi.

    Args:
        mock_get: Requests.get mock'u
        api_instance: FinnhubAPI instance'ı
    """
    # API hatası simülasyonu
    mock_get.side_effect = requests.exceptions.RequestException("API Error")
    
    # Fonksiyonu çağır ve hata yönetimini kontrol et
    api_instance.collect_symbol_data("AAPL")
    
    # Veritabanında kayıt olmamalı
    session = api_instance.db_manager.Session()
    record_count = session.query(StockData).count()
    assert record_count == 0, "Hatalı durumda veri kaydedildi"
    session.close()


def test_rate_limiting(api_instance: FinnhubAPI) -> None:
    """
    Rate limiting testi.

    Args:
        api_instance: FinnhubAPI instance'ı
    """
    start_time = datetime.now()
    
    # Art arda 3 istek yap
    for _ in range(3):
        api_instance.rate_limiter.wait_if_needed()
    
    elapsed_time = (datetime.now() - start_time).total_seconds()
    
    # Rate limiting çalışıyor mu kontrol et
    assert elapsed_time >= 6, "Rate limiting çalışmıyor"


def test_data_validation(api_instance: FinnhubAPI, mock_response: MagicMock) -> None:
    """
    Veri doğrulama testi.

    Args:
        api_instance: FinnhubAPI instance'ı
        mock_response: Mock API yanıtı
    """
    # Geçersiz veri simülasyonu
    mock_response.json.return_value = {"invalid": "data"}
    
    with patch("requests.get", return_value=mock_response):
        api_instance.collect_symbol_data("AAPL")
    
    # Geçersiz veri kaydedilmemeli
    session = api_instance.db_manager.Session()
    record_count = session.query(StockData).count()
    assert record_count == 0, "Geçersiz veri kaydedildi"
    session.close()


if __name__ == "__main__":
    pytest.main(["-v", __file__])