"""Rate limiter module."""

import time
from typing import List


class RateLimiter:
    """Rate limiter class for API requests."""

    def __init__(self, max_requests: int, time_window: int) -> None:
        """Initialize rate limiter.

        Args:
            max_requests: Maximum number of requests allowed in time window
            time_window: Time window in seconds
        """
        if max_requests <= 0:
            raise ValueError("max_requests must be positive")
        if time_window <= 0:
            raise ValueError("time_window must be positive")

        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: List[float] = []

    def wait_if_needed(self) -> None:
        """Wait if rate limit is exceeded."""
        now = time.time()

        # Remove old requests
        self.requests = [
            req_time for req_time in self.requests if now - req_time <= self.time_window
        ]

        # If we've hit the limit, wait
        if len(self.requests) >= self.max_requests:
            oldest_request = self.requests[0]
            wait_time = oldest_request + self.time_window - now
            if wait_time > 0:
                time.sleep(wait_time)
                # Update current time after sleep
                now = time.time()

        # Add current request
        self.requests.append(now)
