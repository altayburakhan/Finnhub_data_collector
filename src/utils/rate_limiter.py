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
    """Implements rate limiting for API requests."""

    def __init__(self, max_requests: int, time_window: int) -> None:
        """Initialize rate limiter.

        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
        """
        self.max_requests: int = max_requests
        self.time_window: int = time_window
        self.requests: Deque[float] = deque()

    def wait_if_needed(self) -> None:
        """Check and wait if rate limit would be exceeded."""
        current_time = time.time()

        # Remove old requests outside the time window
        while self.requests and current_time - self.requests[0] >= self.time_window:
            self.requests.popleft()

        # If at rate limit, wait until oldest request expires
        if len(self.requests) >= self.max_requests:
            wait_time = self.requests[0] + self.time_window - current_time
            if wait_time > 0:
                logger.debug(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)

        # Add current request
        self.requests.append(current_time)
