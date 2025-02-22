"""Data collecting in Finnhub.io."""

import json
import logging
import os
import threading
import time
from datetime import datetime
from queue import Empty, Queue
from typing import Dict, List, Optional, Set, Union, cast

import websocket  # type: ignore
from dotenv import load_dotenv

from src.database.postgres_manager import PostgresManager
from src.utils.rate_limiter import RateLimiter

# Constants
RECONNECT_DELAY: int = 1  # seconds
MAX_RETRIES: int = 3  # reduced from 10 to be more aggressive
MAX_REQUESTS_PER_MINUTE: int = 30
SYNC_INTERVAL: float = 3.0  # seconds between data collections
SYNC_TOLERANCE: float = 0.5  # seconds of tolerance for sync
PING_INTERVAL: int = 5  # reduced from 10 to detect connection issues faster
PING_TIMEOUT: int = 3  # reduced from 5 to reconnect faster
MAX_PING_RETRIES: int = 2  # new constant for ping retry limit
BUFFER_SIZE: int = 100  # maximum number of trades to buffer
BUFFER_TIMEOUT: int = 5  # seconds to wait before processing buffer

# Custom types as dictionary
TradeData = Dict[str, Union[str, float, int]]
WebSocketMessage = Dict[str, Union[str, List[TradeData]]]
StockDataDict = Dict[str, Union[str, float, datetime]]

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
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
        self.last_sync_time: float = 0
        self.last_pong_time: float = 0
        self.collected_symbols: Set[str] = set()
        self.rate_limiter: RateLimiter = RateLimiter(
            max_requests=MAX_REQUESTS_PER_MINUTE, time_window=60
        )
        # Buffer for storing trade data
        self.buffer: Queue = Queue(maxsize=BUFFER_SIZE)
        self.last_buffer_process_time: float = time.time()
        self.connect()

    def should_reconnect(self) -> bool:
        """
        Reconnection check.

        Returns:
            bool: Should reconnect?
        """
        now: float = time.time()
        # Only check delay if we've exceeded max retries
        if self.retry_count >= MAX_RETRIES:
            if now - self.last_connection_time < RECONNECT_DELAY:
                return False
            # Reset retry count after delay
            self.retry_count = 0
        return True

    def connect(self) -> None:
        """Creates the WebSocket connection."""
        if not self.should_reconnect():
            logger.warning(
                f"Waiting for {RECONNECT_DELAY} seconds before reconnecting..."
            )
            time.sleep(RECONNECT_DELAY)
            return

        self.last_connection_time = time.time()
        self.retry_count += 1

        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(
            f"wss://ws.finnhub.io?token={self.api_key}",
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
            on_ping=self.on_ping,
            on_pong=self.on_pong,
        )

    def should_process_message(self, symbol: str) -> bool:
        """
        Check if we should process this symbol's message.

        Args:
            symbol: Stock symbol

        Returns:
            bool: True if we should process the message
        """
        now = time.time()
        time_since_last_sync = now - self.last_sync_time

        # If SYNC_INTERVAL has passed (with tolerance), reset collection
        if time_since_last_sync >= (SYNC_INTERVAL - SYNC_TOLERANCE):
            self.collected_symbols.clear()
            self.last_sync_time = now
            logger.info(f"Starting new collection cycle at {datetime.now()}")
            return True

        # If we haven't collected this symbol in current interval
        if symbol not in self.collected_symbols:
            self.collected_symbols.add(symbol)
            return True

        return False

    def process_buffer(self) -> None:
        """Process buffered trade data."""
        try:
            trades_to_process: List[Dict[str, Union[str, float, datetime]]] = []
            while not self.buffer.empty() and len(trades_to_process) < BUFFER_SIZE:
                try:
                    trade = self.buffer.get_nowait()
                    trades_to_process.append(trade)
                except Empty:
                    break

            if trades_to_process:
                for trade in trades_to_process:
                    # Apply rate limiting
                    self.rate_limiter.wait_if_needed()
                    result = self.db_manager.insert_stock_data(trade)
                    if result:
                        logger.info(
                            "Data saved from buffer: "
                            f"{trade['symbol']} - ${float(trade['price']):.2f}"
                        )

                logger.info(f"Processed {len(trades_to_process)} trades from buffer")
                self.last_buffer_process_time = time.time()

        except Exception as e:
            logger.error(f"Buffer processing error: {str(e)}")

    def buffer_monitor(self) -> None:
        """Monitor and process buffer periodically."""
        while True:
            try:
                now = time.time()
                if (
                    now - self.last_buffer_process_time >= BUFFER_TIMEOUT
                    or self.buffer.qsize() >= BUFFER_SIZE
                ):
                    self.process_buffer()
                time.sleep(0.1)  # Small delay to prevent CPU overuse
            except Exception as e:
                logger.error(f"Buffer monitor error: {str(e)}")
                time.sleep(1)

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

                    # Only process if we haven't collected this symbol yet
                    if not self.should_process_message(symbol):
                        continue

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

                    # Add to buffer instead of direct database insert
                    try:
                        self.buffer.put_nowait(stock_data)
                        logger.debug(
                            f"Added to buffer: {symbol} - ${price:.2f} "
                            f"(Buffer size: {self.buffer.qsize()})"
                        )
                    except Exception as e:
                        logger.error(f"Buffer error: {str(e)}")

                # Check if we've collected all symbols
                if len(self.collected_symbols) == len(self.symbols):
                    logger.info("Collected data for all symbols in this cycle")

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
            time.sleep(RECONNECT_DELAY * 2)  # Wait longer for rate limit
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
        logger.warning(
            f"WebSocket connection closed (code: {close_status_code}, msg: {close_msg})"
        )
        # Reset the WebSocket instance
        self.ws = None
        # Try to reconnect immediately
        self.connect()
        if self.ws:
            self.ws.run_forever(ping_interval=PING_INTERVAL, ping_timeout=PING_TIMEOUT)

    def on_open(self, ws: websocket.WebSocketApp) -> None:
        """
        Processes WebSocket connection opening.

        Args:
            ws: WebSocket connection
        """
        logger.info("WebSocket connection opened")
        # Reset retry count on successful connection
        self.retry_count = 0
        self.last_sync_time = time.time()
        self.last_pong_time = time.time()
        self.collected_symbols.clear()

        # Subscribe to all symbols at once
        for symbol in self.symbols:
            self.rate_limiter.wait_if_needed()
            ws.send(json.dumps({"type": "subscribe", "symbol": symbol}))
            logger.info(f"Subscription started for {symbol}")

    def on_ping(self, ws: websocket.WebSocketApp, message: str) -> None:
        """
        Handle ping message from server.

        Args:
            ws: WebSocket connection
            message: Ping message
        """
        logger.debug("Received ping")
        if ws:
            ws.send(message, opcode=0xA)  # 0xA is the opcode for PONG

    def on_pong(self, ws: websocket.WebSocketApp, message: str) -> None:
        """
        Handle pong message from server.

        Args:
            ws: WebSocket connection
            message: Pong message
        """
        logger.debug("Received pong")
        self.last_pong_time = time.time()

    def check_connection(self) -> None:
        """Check connection health using ping/pong."""
        ping_failures = 0
        while True:
            try:
                now = time.time()
                if now - self.last_pong_time > PING_TIMEOUT:
                    ping_failures += 1
                    logger.warning(
                        f"Ping timeout {ping_failures}/{MAX_PING_RETRIES}, "
                        f"last pong: {now - self.last_pong_time:.1f}s ago"
                    )
                    if ping_failures >= MAX_PING_RETRIES:
                        logger.warning("Max ping retries exceeded, reconnecting...")
                        if self.ws:
                            self.ws.close()
                        ping_failures = 0
                else:
                    ping_failures = 0  # Reset counter on successful pong
                time.sleep(PING_INTERVAL / 2)  # Check more frequently
            except Exception as e:
                logger.error(f"Connection check error: {str(e)}")
                time.sleep(1)

    def run(self) -> None:
        """Starts the WebSocket connection."""
        # Start connection health check in a separate thread
        health_check = threading.Thread(target=self.check_connection)
        health_check.daemon = True
        health_check.start()

        # Start buffer monitor in a separate thread
        buffer_monitor = threading.Thread(target=self.buffer_monitor)
        buffer_monitor.daemon = True
        buffer_monitor.start()

        while True:
            try:
                if self.ws:
                    self.ws.run_forever(
                        ping_interval=PING_INTERVAL, ping_timeout=PING_TIMEOUT
                    )
                else:
                    self.connect()
                time.sleep(0.1)  # Small delay between reconnection attempts
            except Exception as e:
                logger.error(f"WebSocket run error: {str(e)}")
                time.sleep(0.1)


def main() -> None:
    """Main application function."""
    ws_client = FinnhubWebSocket()
    ws_client.run()


if __name__ == "__main__":
    main()
