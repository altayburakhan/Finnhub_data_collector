"""Rate limiter implementation for API requests.

This module provides rate limiting functionality to prevent
exceeding API rate limits.
"""

import logging
import time
from typing import List

logger = logging.getLogger(__name__)

class RateLimiter:
    """Implements rate limiting for API requests."""

    def __init__(self, max_requests: int = 30, time_window: int = 60):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
        """
        if max_requests <= 0 or time_window <= 0:
            raise ValueError("max_requests and time_window must be positive")
            
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: List[float] = []

    def wait_if_needed(self) -> None:
        """Check and wait if rate limit would be exceeded."""
        current_time = time.time()
        
        # Clean old requests
        self.requests = [req for req in self.requests 
                        if current_time - req < self.time_window]
        
        # Wait if max requests reached
        if len(self.requests) >= self.max_requests:
            oldest_request = self.requests[0]
            wait_time = oldest_request + self.time_window - current_time
            if wait_time > 0:
                logger.debug(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
            self.requests = self.requests[1:]
        
        # Add current request
        self.requests.append(time.time())
