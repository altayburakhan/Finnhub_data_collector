"""Finnhub.io'dan veri toplama modülü."""

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, Optional

import websocket
from dotenv import load_dotenv

from src.database.postgres_manager import PostgresManager

# Sabitler
RECONNECT_DELAY = 60  # saniye
MAX_RETRIES = 3

# Log yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# .env dosyasını yükle
load_dotenv()


class FinnhubWebSocket:
    """Finnhub WebSocket bağlantısını yöneten sınıf."""

    def __init__(self) -> None:
        """WebSocket bağlantısını başlat."""
        self.api_key = os.getenv('FINNHUB_API_KEY')
        if not self.api_key:
            raise ValueError("FINNHUB_API_KEY bulunamadı!")

        self.symbols = [
            'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META',
            'TSLA', 'NVDA', 'AMD', 'INTC', 'NFLX'
        ]
        self.db_manager = PostgresManager()
        self.ws = None
        self.retry_count = 0
        self.last_connection_time = 0
        self.connect()

    def should_reconnect(self) -> bool:
        """
        Yeniden bağlanma kontrolü.

        Returns:
            bool: Yeniden bağlanılmalı mı
        """
        now = time.time()
        if now - self.last_connection_time < RECONNECT_DELAY:
            return False
        return self.retry_count < MAX_RETRIES

    def connect(self) -> None:
        """WebSocket bağlantısını oluştur."""
        if not self.should_reconnect():
            logger.warning(
                f"Rate limit nedeniyle {RECONNECT_DELAY} saniye bekleniyor..."
            )
            time.sleep(RECONNECT_DELAY)
            self.retry_count = 0
            
        self.last_connection_time = time.time()
        self.retry_count += 1
        
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(
            f"wss://ws.finnhub.io?token={self.api_key}",
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )

    def on_message(self, ws: websocket.WebSocketApp, message: str) -> None:
        """
        WebSocket mesajını işle.

        Args:
            ws: WebSocket bağlantısı
            message: Gelen mesaj
        """
        try:
            data = json.loads(message)
            if data['type'] == 'trade':
                for trade in data['data']:
                    stock_data = {
                        'symbol': trade['s'],
                        'price': float(trade['p']),
                        'volume': float(trade['v']),
                        'timestamp': datetime.fromtimestamp(
                            trade['t'] / 1000
                        ).strftime('%Y-%m-%d %H:%M:%S'),
                        'collected_at': datetime.now().isoformat()
                    }
                    
                    result = self.db_manager.insert_stock_data(stock_data)
                    if result:
                        logger.info(
                            f"Veri kaydedildi: {stock_data['symbol']} - "
                            f"${stock_data['price']:.2f}"
                        )

        except Exception as e:
            logger.error(f"Mesaj işleme hatası: {str(e)}")

    def on_error(self, ws: websocket.WebSocketApp, error: str) -> None:
        """
        WebSocket hatasını işle.

        Args:
            ws: WebSocket bağlantısı
            error: Hata mesajı
        """
        if "429" in str(error):  # Rate limit hatası
            logger.warning("Rate limit aşıldı, bekleniyor...")
            time.sleep(RECONNECT_DELAY)
        else:
            logger.error(f"WebSocket hatası: {str(error)}")

    def on_close(self, ws: websocket.WebSocketApp, 
                close_status_code: int, close_msg: str) -> None:
        """
        WebSocket bağlantısı kapandığında çalışır.

        Args:
            ws: WebSocket bağlantısı
            close_status_code: Kapanma durum kodu
            close_msg: Kapanma mesajı
        """
        logger.warning("WebSocket bağlantısı kapandı")
        if self.should_reconnect():
            self.connect()
            self.ws.run_forever()
        else:
            logger.error("Maksimum yeniden bağlanma denemesi aşıldı")

    def on_open(self, ws: websocket.WebSocketApp) -> None:
        """
        WebSocket bağlantısı açıldığında çalışır.

        Args:
            ws: WebSocket bağlantısı
        """
        logger.info("WebSocket bağlantısı açıldı")
        # Sembollere sırayla abone ol
        for symbol in self.symbols:
            ws.send(json.dumps({'type': 'subscribe', 'symbol': symbol}))
            logger.info(f"{symbol} için abonelik başlatıldı")
            time.sleep(1)  # Rate limit'i aşmamak için bekle

    def run(self) -> None:
        """WebSocket bağlantısını başlat."""
        while True:
            try:
                self.ws.run_forever()
                if not self.should_reconnect():
                    logger.error("Bağlantı kurulamıyor, uygulama durduruluyor")
                    break
            except Exception as e:
                logger.error(f"WebSocket çalıştırma hatası: {str(e)}")
                time.sleep(1)


def main() -> None:
    """Ana uygulama fonksiyonu."""
    ws_client = FinnhubWebSocket()
    ws_client.run()


if __name__ == "__main__":
    main()