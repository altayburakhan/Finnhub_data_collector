import os
import sys

# Projenin kök dizinini Python path'ine ekle
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from database.postgres_manager import PostgresManager
import pandas as pd

def check_database():
    db = PostgresManager()
    
    # Veritabanı bağlantısı oluştur
    engine = db.engine
    
    # Verileri kontrol et
    query = "SELECT COUNT(*) as count FROM stock_data"
    result = pd.read_sql(query, engine)
    print(f"Veritabanındaki toplam kayıt sayısı: {result['count'].iloc[0]}")
    
    # Son 5 kaydı göster
    query = "SELECT * FROM stock_data ORDER BY collected_at DESC LIMIT 5"
    recent_data = pd.read_sql(query, engine)
    print("\nSon 5 kayıt:")
    print(recent_data)

if __name__ == "__main__":
    check_database()