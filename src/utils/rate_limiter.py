"""Rate limiter implementation for API requests.

This module provides rate limiting functionality to prevent
exceeding API rate limits.
"""

import logging
import time
from collections import deque
from typing import Deque

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter using token bucket algorithm."""

    def __init__(self, max_requests: int, time_window: int) -> None:
        """Initialize rate limiter.

        Args:
            max_requests: Maximum number of requests allowed in time window
            time_window: Time window in seconds

        Raises:
            ValueError: If max_requests or time_window is not positive
        """
        if max_requests <= 0 or time_window <= 0:
            raise ValueError("max_requests and time_window must be positive")

        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Deque[float] = deque()

    def wait_if_needed(self) -> None:
        """Wait if rate limit is exceeded."""
        now = time.time()

        # Remove old requests
        while self.requests and now - self.requests[0] > self.time_window:
            self.requests.popleft()

        # If we've hit the limit, wait
        if len(self.requests) >= self.max_requests:
            wait_time = self.requests[0] + self.time_window - now
            if wait_time > 0:
                logger.info(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                # After waiting, remove old requests again
                now = time.time()
                while self.requests and now - self.requests[0] > self.time_window:
                    self.requests.popleft()

        # Add current request
        self.requests.append(now)
