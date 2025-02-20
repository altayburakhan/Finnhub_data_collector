import pytest
from unittest.mock import Mock, patch
from main import FinnhubAPI

@pytest.fixture
def mock_response():
    """Mock API response"""
    return {
        'c': 100.0,  # Current price
        't': 1582641000  # Timestamp
    }

@pytest.fixture
def api(db_manager):  # db_manager'ı parametre olarak al
    """FinnhubAPI instance'ı"""
    api = FinnhubAPI()
    api.db_manager = db_manager  # Test db manager'ı kullan
    return api

@patch('requests.get')
def test_collect_data_success(mock_get, api, mock_response):
    """Veri toplama testi"""
    # Mock response ayarla
    mock_get.return_value.json.return_value = mock_response
    mock_get.return_value.raise_for_status = Mock()
    
    # Veri topla
    api.collect_data()
    
    # Her sembol için bir çağrı yapılmış olmalı
    assert mock_get.call_count == len(api.symbols)

    # En az bir kayıt eklenmiş olmalı
    records = api.db_manager.get_latest_records(limit=1)
    assert len(records) > 0