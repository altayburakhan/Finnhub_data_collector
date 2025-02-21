"""Data collecting in Finnhub.io."""

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Union, cast

import websocket  # type: ignore
from dotenv import load_dotenv

from src.database.postgres_manager import PostgresManager
from src.utils.rate_limiter import RateLimiter

# Constants
RECONNECT_DELAY: int = 60  # seconds
MAX_RETRIES: int = 3
MAX_REQUESTS_PER_MINUTE: int = 20

# Custom types as dictionary
TradeData = Dict[str, Union[str, float, int]]
WebSocketMessage = Dict[str, Union[str, List[TradeData]]]
StockDataDict = Dict[str, Union[str, float, datetime]]

# Logging configuration
logging.basicConfig(
    level=logging.INFO,  # every message will be logged
    format=("%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
)
logger = logging.getLogger(__name__)

# Load .env file
load_dotenv()


class FinnhubWebSocket:
    """Manages the Finnhub WebSocket connection."""

    def __init__(self) -> None:
        """Starts the WebSocket connection."""
        self.api_key: Optional[str] = os.getenv("FINNHUB_API_KEY")
        if not self.api_key:
            raise ValueError("FINNHUB_API_KEY not found!")

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
        self.rate_limiter: RateLimiter = RateLimiter(
            max_requests=MAX_REQUESTS_PER_MINUTE, time_window=60
        )
        self.connect()

    def should_reconnect(self) -> bool:
        """
        Reconnection check.

        Returns:
            bool: Should reconnect?
        """
        now: float = time.time()
        if now - self.last_connection_time < RECONNECT_DELAY:
            return False
        return self.retry_count < MAX_RETRIES

    def connect(self) -> None:
        """Creates the WebSocket connection."""
        if not self.should_reconnect():
            logger.warning(
                f"Waiting for {RECONNECT_DELAY} seconds due to rate limit..."
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
        """Processes WebSocket message.

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

                    # Apply rate limiting
                    self.rate_limiter.wait_if_needed()
                    result = self.db_manager.insert_stock_data(stock_data)
                    if result:
                        logger.info(f"Data saved: {symbol} - ${price:.2f}")

        except Exception as e:
            logger.error(f"Message processing error: {str(e)}")

    def on_error(self, ws: websocket.WebSocketApp, error: str) -> None:
        """
        Processes WebSocket error.

        Args:
            ws: WebSocket connection
            error: Error message
        """
        if "429" in str(error):  # Rate limit error
            logger.warning("Rate limit exceeded, waiting...")
            time.sleep(RECONNECT_DELAY)
        else:
            logger.error(f"WebSocket error: {str(error)}")

    def on_close(
        self,
        ws: websocket.WebSocketApp,
        close_status_code: Optional[int],
        close_msg: Optional[str],
    ) -> None:
        """
        Processes WebSocket connection closure.

        Args:
            ws: WebSocket connection
            close_status_code: Closure status code
            close_msg: Closure message
        """
        logger.warning("WebSocket connection closed")
        if self.should_reconnect():
            self.connect()
            if self.ws:
                self.ws.run_forever()
        else:
            logger.error("Maximum reconnection attempts exceeded")

    def on_open(self, ws: websocket.WebSocketApp) -> None:
        """
        Processes WebSocket connection opening.

        Args:
            ws: WebSocket connection
        """
        logger.info("WebSocket connection opened")
        # Subscribe to symbols one by one with rate limiting
        for symbol in self.symbols:
            self.rate_limiter.wait_if_needed()
            ws.send(json.dumps({"type": "subscribe", "symbol": symbol}))
            logger.info(f"Subscription started for {symbol}")

    def run(self) -> None:
        """Starts the WebSocket connection."""
        while True:
            try:
                if self.ws:
                    self.ws.run_forever()
                if not self.should_reconnect():
                    logger.error(
                        "Connection could not be established, application stopped"
                    )
                    break
            except Exception as e:
                logger.error(f"WebSocket run error: {str(e)}")
                time.sleep(1)


def main() -> None:
    """Main application function."""
    ws_client = FinnhubWebSocket()
    ws_client.run()


if __name__ == "__main__":
    main()
