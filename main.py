"""My real-time stock data collector using Finnhub.io.

This is my first Python project. It streams data using WebSocket and
stores it in PostgreSQL. Through this project, I've gained experience
with WebSocket, database management, and data processing.
"""

import json
import logging
import os
import threading
import time
from datetime import datetime
from queue import Empty, Queue
from typing import Dict, List, Optional, Set, Union, cast, Any

import websocket
from dotenv import load_dotenv

from src.database.postgres_manager import PostgresManager
from src.utils.rate_limiter import RateLimiter

RECONNECT_DELAY: int = 5
MAX_RETRIES: int = 5
MAX_REQUESTS_PER_MINUTE: int = 30
SYNC_INTERVAL: float = 3.0
SYNC_TOLERANCE: float = 0.5
PING_INTERVAL: int = 10
PING_TIMEOUT: int = 5
MAX_PING_RETRIES: int = 3
BUFFER_SIZE: int = 100
BUFFER_TIMEOUT: int = 5
RATE_LIMIT_WAIT: int = 60  # 60 saniye bekle

StockData = Dict[str, Any]  # Holds any stock related data
TradeMessage = Dict[str, Any]  # Holds websocket messages

logging.basicConfig(
    level=logging.INFO,
    format=("%(asctime)s - %(levelname)s - %(message)s"),
)
logger = logging.getLogger(__name__)
# Websocket debug loglarını kapatalım
logging.getLogger('websocket').setLevel(logging.WARNING)

# Load .env file
load_dotenv()


class FinnhubWebSocket:
    """My main class for managing WebSocket connection.

    This class establishes a WebSocket connection to Finnhub.io,
    processes incoming data, and stores it in the database. It handles
    connection management, data processing, and error handling.
    """

    def __init__(self) -> None:
        """Set up WebSocket connection and required components.

        Initialize API key, stock symbols to track, and helper tools
        like buffer and rate limiter.
        """
        self.api_key: str = os.getenv("FINNHUB_API_KEY", "")
        if not self.api_key:
            raise ValueError("FINNHUB_API_KEY not found!")

        self.symbols: List[str] = [
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "META",
            "TSLA",
            "NVDA",
            "AMD",
            "INTC",
            "NFLX"
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
        """Check if reconnection should be attempted.

        Before attempting to reconnect after a connection drop,
        check retry count and timing.

        Returns:
            bool: Whether to attempt reconnection
        """
        now: float = time.time()
        if self.retry_count >= MAX_RETRIES:
            if now - self.last_connection_time < RECONNECT_DELAY:
                return False
            self.retry_count = 0
        return True

    def connect(self) -> None:
        """Establish WebSocket connection.

        Create WebSocket connection to Finnhub.io and set up
        connection parameters and ping/pong mechanism.
        """
        if not self.should_reconnect():
            logger.warning(
                f"Waiting for {RECONNECT_DELAY} seconds before reconnecting..."
            )
            time.sleep(RECONNECT_DELAY)
            return

        self.last_connection_time = time.time()
        self.retry_count += 1

        try:
            websocket.enableTrace(False)  # Debug mesajlarını kapatalım
            self.ws = websocket.WebSocketApp(
                f"wss://ws.finnhub.io?token={self.api_key}",
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open,
                on_ping=self.on_ping,
                on_pong=self.on_pong,
            )

            logger.info("Attempting to establish WebSocket connection...")
            # Add connection parameters
            self.ws.run_forever(
                ping_interval=PING_INTERVAL,
                ping_timeout=PING_TIMEOUT,
                ping_payload="ping",
            )
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            time.sleep(RECONNECT_DELAY)
            self.connect()

    def should_process_message(self, symbol: str) -> bool:
        """Check if a message should be processed.

        For each symbol, decide whether to process the incoming
        message based on collection intervals.

        Args:
            symbol: Stock symbol to check

        Returns:
            bool: Whether to process the message
        """
        now = time.time()
        time_since_last_sync = now - self.last_sync_time

        if time_since_last_sync >= (SYNC_INTERVAL - SYNC_TOLERANCE):
            self.collected_symbols.clear()
            self.last_sync_time = now
            logger.info(f"Starting new collection cycle at {datetime.now()}")
            return True

        if symbol not in self.collected_symbols:
            self.collected_symbols.add(symbol)
            return True

        return False

    def process_buffer(self) -> None:
        """Process buffered data.

        Save accumulated data from buffer to database in batches
        for better database connection efficiency.
        """
        try:
            trades_to_process: List[Dict[str, Union[str, float, datetime]]] = []
            while not self.buffer.empty() and len(trades_to_process) < BUFFER_SIZE:
                try:
                    trade = self.buffer.get_nowait()
                    trades_to_process.append(trade)
                except Empty:
                    break

            if trades_to_process:
                logger.info(f"Attempting to process {len(trades_to_process)} trades from buffer")
                success_count = 0
                for trade in trades_to_process:
                    self.rate_limiter.wait_if_needed()
                    result = self.db_manager.insert_stock_data(trade)
                    if result:
                        success_count += 1
                        logger.info(
                            f"✓ Saved to DB: {trade['symbol']} - ${float(trade['price']):.2f} "
                            f"(Volume: {trade['volume']}, Time: {trade['timestamp']})"
                        )
                    else:
                        logger.error(
                            f"✗ Failed to save: {trade['symbol']} - ${float(trade['price']):.2f}"
                        )

                logger.info(f"Successfully processed {success_count}/{len(trades_to_process)} trades")
                self.last_buffer_process_time = time.time()

        except Exception as e:
            logger.error(f"Buffer processing error: {str(e)}")

    def buffer_monitor(self) -> None:
        """Monitor buffer status.

        Continuously check buffer status and call process_buffer
        when it's full or timeout is reached.
        """
        logger.info("Buffer monitor started")
        while True:
            try:
                now = time.time()
                if (
                    now - self.last_buffer_process_time >= BUFFER_TIMEOUT
                    or self.buffer.qsize() >= BUFFER_SIZE
                ):
                    logger.info(f"Buffer size: {self.buffer.qsize()}")
                    self.process_buffer()
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Buffer monitor error: {str(e)}")
                time.sleep(1)

    def on_message(self, ws: websocket.WebSocketApp, message: str) -> None:
        """Process incoming WebSocket messages.

        Args:
            ws: WebSocket connection object
            message: Incoming message
        """
        try:
            data: TradeMessage = json.loads(message)
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

                    stock_data: StockData = {
                        "symbol": symbol,
                        "price": price,
                        "volume": volume,
                        "timestamp": timestamp,
                        "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }

                    try:
                        self.buffer.put_nowait(stock_data)
                        logger.debug(
                            f"Added to buffer: {symbol} - ${price:.2f} "
                            f"(Buffer size: {self.buffer.qsize()})"
                        )
                    except Exception as e:
                        logger.error(f"Buffer error: {str(e)}")

                if len(self.collected_symbols) == len(self.symbols):
                    logger.info("Collected data for all symbols in this cycle")
                    # Force buffer processing when we have all symbols
                    if self.buffer.qsize() > 0:
                        self.process_buffer()

        except Exception as e:
            logger.error(f"Message processing error: {str(e)}")

    def on_error(self, ws: websocket.WebSocketApp, error: str) -> None:
        """Handle WebSocket errors.

        Args:
            ws: WebSocket connection object
            error: Error message
        """
        if "429" in str(error):
            logger.warning(f"Rate limit exceeded, waiting {RATE_LIMIT_WAIT} seconds...")
            time.sleep(RATE_LIMIT_WAIT)
            if self.ws:
                self.ws.close()
                self.ws = None
            self.connect()
        else:
            logger.error(f"WebSocket error: {str(error)}")
            if self.ws:
                self.ws.close()
                self.ws = None
            time.sleep(RECONNECT_DELAY)
            self.connect()

    def on_close(
        self,
        ws: websocket.WebSocketApp,
        close_status_code: Optional[int],
        close_msg: Optional[str],
    ) -> None:
        """Handle WebSocket connection closure.

        Args:
            ws: WebSocket connection object
            close_status_code: Connection close status code
            close_msg: Connection close message
        """
        logger.warning(
            f"WebSocket connection closed (code: {close_status_code}, msg: {close_msg})"
        )
        self.ws = None
        time.sleep(RECONNECT_DELAY)
        self.connect()

    def on_open(self, ws: websocket.WebSocketApp) -> None:
        """Handle WebSocket connection opening.

        Args:
            ws: WebSocket connection object
        """
        logger.info("WebSocket connection opened")
        # Reset retry count on successful connection
        self.retry_count = 0
        self.last_sync_time = time.time()
        self.last_pong_time = time.time()
        self.collected_symbols.clear()

        # Subscribe to symbols with delay to avoid rate limit
        for symbol in self.symbols:
            self.rate_limiter.wait_if_needed()
            time.sleep(0.5)  # Her istek arasında yarım saniye bekle
            ws.send(json.dumps({"type": "subscribe", "symbol": symbol}))
            logger.info(f"Subscription started for {symbol}")

    def on_ping(self, ws: websocket.WebSocketApp, message: str) -> None:
        """Handle ping messages.

        Args:
            ws: WebSocket connection object
            message: Ping message
        """
        logger.debug("Received ping")
        if ws:
            ws.send(message, opcode=0xA)

    def on_pong(self, ws: websocket.WebSocketApp, message: str) -> None:
        """Handle pong messages.

        Args:
            ws: WebSocket connection object
            message: Pong message
        """
        logger.debug("Received pong")
        self.last_pong_time = time.time()

    def check_connection(self) -> None:
        """Monitor connection health.

        Check connection health using ping/pong mechanism and
        initiate reconnection when needed.
        """
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
                    ping_failures = 0
                time.sleep(PING_INTERVAL / 2)
            except Exception as e:
                logger.error(f"Connection check error: {str(e)}")
                time.sleep(1)

    def run(self) -> None:
        """Start the application.

        Create connection health check and buffer monitor threads,
        then start WebSocket connection.
        """
        try:
            logger.info("Starting Finnhub WebSocket client...")
            
            # Start health check thread
            health_check = threading.Thread(target=self.check_connection)
            health_check.daemon = True
            health_check.start()
            logger.info("Connection health check thread started")

            # Start buffer monitor thread
            buffer_monitor = threading.Thread(target=self.buffer_monitor)
            buffer_monitor.daemon = True
            buffer_monitor.start()
            logger.info("Buffer monitor thread started")

            while True:
                try:
                    if self.ws:
                        self.ws.run_forever(
                            ping_interval=PING_INTERVAL,
                            ping_timeout=PING_TIMEOUT,
                            ping_payload="ping",
                        )
                    else:
                        self.connect()
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"WebSocket run error: {str(e)}")
                    time.sleep(RECONNECT_DELAY)
                    continue

        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            raise


def main() -> None:
    """Run the main application."""
    try:
        # Test database connection first
        db_manager = PostgresManager()
        db_manager.create_table()
        logger.info("Database connection test successful!")
        
        # Initialize and run WebSocket client
        finnhub_client = FinnhubWebSocket()
        
        # Start buffer monitor in a separate thread
        buffer_monitor_thread = threading.Thread(
            target=finnhub_client.buffer_monitor,
            daemon=True
        )
        buffer_monitor_thread.start()
        
        # Start connection checker in a separate thread
        connection_checker_thread = threading.Thread(
            target=finnhub_client.check_connection,
            daemon=True
        )
        connection_checker_thread.start()
        
        # Run the main WebSocket client
        finnhub_client.run()
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
