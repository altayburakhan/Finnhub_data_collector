import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Proje kök dizinini Python path'ine ekle
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from src.database.postgres_manager import Base, PostgresManager

load_dotenv()

@pytest.fixture(scope="session")
def test_db_url():
    """Test veritabanı URL'si"""
    return (
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@"
        f"{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/test_finnhub_db"
    )

@pytest.fixture(scope="session")
def test_engine(test_db_url):
    """Test veritabanı engine'i"""
    engine = create_engine(test_db_url)
    
    # Mevcut bağlantıları kapat ve tabloyu yeniden oluştur
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Testler bitince tabloları temizle
    Base.metadata.drop_all(engine)

@pytest.fixture
def test_session(test_engine):
    """Test session'ı"""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def db_manager(test_engine):
    """Test için PostgresManager instance'ı"""
    manager = PostgresManager()
    manager.engine = test_engine
    manager.Session = sessionmaker(bind=test_engine)
    return manager

@pytest.fixture
def sample_stock_data():
    """Örnek hisse senedi verisi"""
    return {
        'symbol': 'TEST',
        'price': 100.0,
        'volume': 1000,
        'timestamp': '2024-02-20 12:00:00',
        'collected_at': '2024-02-20T12:00:00'
    }