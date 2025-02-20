from postgres_manager import PostgresManager, Base

def reset_database():
    db = PostgresManager()
    
    # Tüm tabloları sil ve yeniden oluştur
    Base.metadata.drop_all(db.engine)
    Base.metadata.create_all(db.engine)
    print("Veritabanı başarıyla sıfırlandı!")

if __name__ == "__main__":
    reset_database()