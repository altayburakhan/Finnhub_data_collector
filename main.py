"""Finnhub.io'dan veri toplama modülü."""

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Union, cast

import websocket  # type: ignore
from dotenv import load_dotenv

from src.database.postgres_manager import PostgresManager

# Sabitler
RECONNECT_DELAY: int = 60  # saniye
MAX_RETRIES: int = 3
MAX_REQUESTS_PER_MINUTE: int = 20

# Custom types
TradeData = Dict[str, Union[str, float, int]]
WebSocketMessage = Dict[str, Union[str, List[TradeData]]]
StockDataDict = Dict[str, Union[str, float, datetime]]

# Log yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format=("%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
)
logger = logging.getLogger(__name__)

# .env dosyasını yükle
load_dotenv()


class FinnhubWebSocket:
    """Finnhub WebSocket bağlantısını yöneten sınıf."""

    def __init__(self) -> None:
        """WebSocket bağlantısını başlat."""
        self.api_key: Optional[str] = os.getenv("FINNHUB_API_KEY")
        if not self.api_key:
            raise ValueError("FINNHUB_API_KEY bulunamadı!")

        self.symbols: List[str] = [
            "AAPL",
            "MSFT",
            "AMZN",
            "GOOGL",
            "META",
            "TSLA",
            "NVDA",
            "AMD",
            "INTC",
            "NFLX",
        ]
        self.db_manager: PostgresManager = PostgresManager()
        self.ws: Optional[websocket.WebSocketApp] = None
        self.retry_count: int = 0
        self.last_connection_time: float = 0
        self.connect()

    def should_reconnect(self) -> bool:
        """
        Yeniden bağlanma kontrolü.

        Returns:
            bool: Yeniden bağlanılmalı mı
        """
        now: float = time.time()
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
            on_open=self.on_open,
        )

    def on_message(self, ws: websocket.WebSocketApp, message: str) -> None:
        """
        Processes WebSocket message.

        Args:
            ws: WebSocket connection
            message: Incoming message
        """
        try:
            data: WebSocketMessage = json.loads(message)
            if data["type"] == "trade":
                trades = cast(List[Dict[str, Union[str, float, int]]], data["data"])
                for trade in trades:
                    symbol = str(trade["s"])
                    price = float(trade["p"])
                    volume = float(trade["v"])
                    timestamp = datetime.fromtimestamp(int(trade["t"]) / 1000).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

                    stock_data: StockDataDict = {
                        "symbol": symbol,
                        "price": price,
                        "volume": volume,
                        "timestamp": timestamp,
                        "collected_at": datetime.now().isoformat(),
                    }

                    result = self.db_manager.insert_stock_data(stock_data)
                    if result:
                        logger.info(f"Data saved: {symbol} - ${price:.2f}")

        except Exception as e:
            logger.error(f"Message processing error: {str(e)}")

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

    def on_close(
        self,
        ws: websocket.WebSocketApp,
        close_status_code: Optional[int],
        close_msg: Optional[str],
    ) -> None:
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
            if self.ws:
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
            ws.send(json.dumps({"type": "subscribe", "symbol": symbol}))
            logger.info(f"{symbol} için abonelik başlatıldı")
            time.sleep(1)  # Rate limit'i aşmamak için bekle

    def run(self) -> None:
        """WebSocket bağlantısını başlat."""
        while True:
            try:
                if self.ws:
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
