import requests
import time
from datetime import datetime
import logging
from src.database.postgres_manager import PostgresManager
from dotenv import load_dotenv
import os
from typing import Dict, Optional
from collections import deque
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

class RateLimiter:
    def __init__(self, max_requests: int, time_window: int):
        """
        Args:
            max_requests (int): Maksimum istek sayısı
            time_window (int): Zaman penceresi (saniye)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()

    def wait_if_needed(self):
        """Rate limit kontrolü yap ve gerekirse bekle"""
        now = datetime.now()
        
        # Eski istekleri temizle
        while self.requests and self.requests[0] < now - timedelta(seconds=self.time_window):
            self.requests.popleft()
        
        # Eğer limit doluysa bekle
        if len(self.requests) >= self.max_requests:
            wait_time = (self.requests[0] + timedelta(seconds=self.time_window) - now).total_seconds()
            if wait_time > 0:
                logger.debug(f"Rate limit nedeniyle {wait_time:.2f} saniye bekleniyor")
                time.sleep(wait_time)
        
        # Yeni isteği kaydet
        self.requests.append(now)

class FinnhubAPI:
    def __init__(self):
        self.api_key = os.getenv('FINNHUB_API_KEY')
        if not self.api_key:
            raise ValueError("FINNHUB_API_KEY bulunamadı!")
            
        self.base_url = "https://finnhub.io/api/v1"
        # Daha fazla sembol ekleyelim
        self.symbols = [
            'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META',
            'TSLA', 'NVDA', 'AMD', 'INTC', 'NFLX',
            'PYPL', 'ADBE', 'CSCO', 'CMCSA', 'PEP',
            'AVGO', 'TXN', 'QCOM', 'INTU', 'AMAT'
        ]
        self.db_manager = PostgresManager()
        # 60 saniye içinde 20 istek için rate limiter
        self.rate_limiter = RateLimiter(max_requests=20, time_window=60)

    def get_quote(self, symbol: str) -> Dict:
        """
        Bir sembol için anlık fiyat verisi al
        
        Args:
            symbol: Hisse senedi sembolü
            
        Returns:
            Dict: Fiyat verisi
        """
        self.rate_limiter.wait_if_needed()
        
        endpoint = f"{self.base_url}/quote"
        params = {
            'symbol': symbol,
            'token': self.api_key
        }
        
        response = requests.get(endpoint, params=params)
        response.raise_for_status()  # HTTP hataları için
        return response.json()

    def collect_data(self) -> None:
        """Tüm semboller için veri topla"""
        logger.info("Veri toplama başladı")
        success_count = 0
        
        for symbol in self.symbols:
            try:
                data = self.get_quote(symbol)
                
                if data.get('c') is None:  # 'c' current price'ı temsil eder
                    logger.warning(f"Geçersiz veri alındı ({symbol}): {data}")
                    continue
                    
                stock_data = {
                    'symbol': symbol,
                    'price': float(data['c']),  # Current price
                    'volume': float(data.get('t', 0)),  # Timestamp'i volume olarak kullan
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'collected_at': datetime.now().isoformat()
                }
                
                result = self.db_manager.insert_stock_data(stock_data)
                if result:
                    success_count += 1
                    logger.info(f"Veri kaydedildi: {symbol} - ${stock_data['price']:.2f} (ID: {result.id})")
                else:
                    logger.error(f"Veri kaydedilemedi: {stock_data}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"HTTP isteği hatası ({symbol}): {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Beklenmeyen hata ({symbol}): {e}", exc_info=True)
                logger.debug(f"Hata oluşturan veri: {data}")  # Debug için veriyi logla
        
        logger.info(f"Veri toplama tamamlandı. Başarılı: {success_count}/{len(self.symbols)}")

def main():
    api = FinnhubAPI()
    
    while True:
        try:
            start_time = time.time()
            api.collect_data()
            
            # 3 saniye bekle (dakikada 20 istek için)
            elapsed = time.time() - start_time
            if elapsed < 3:  # Her 3 saniyede bir çalıştır
                time.sleep(3 - elapsed)
                
        except Exception as e:
            logger.error(f"Ana döngü hatası: {e}", exc_info=True)
            time.sleep(5)

if __name__ == "__main__":
    main()