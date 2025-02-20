import os
import sys
import logging
from datetime import datetime

# Projenin kök dizinini Python path'ine ekle
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(project_root)

from src.database.postgres_manager import PostgresManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_db_connection():
    try:
        logger.info("Veritabanı bağlantısı test ediliyor...")
        db = PostgresManager()
        
        # Test verisi ekle
        test_data = {
            'symbol': 'TEST',
            'price': 100.0,
            'volume': 1000,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'collected_at': datetime.now().isoformat()
        }
        
        logger.info(f"Test verisi ekleniyor: {test_data}")
        result = db.insert_stock_data(test_data)
        
        if result:
            logger.info(f"Test verisi başarıyla eklendi! ID: {result.id}")
            logger.info(f"Eklenen veri: {result}")
            return True
        else:
            logger.error("Test verisi eklenemedi!")
            return False
            
    except Exception as e:
        logger.error(f"Test sırasında hata: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_db_connection()
    if success:
        print("\nVeritabanı bağlantı testi BAŞARILI!")
    else:
        print("\nVeritabanı bağlantı testi BAŞARISIZ!")