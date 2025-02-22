"""My helper module for limiting API requests.

I use this to control request rates and prevent exceeding API limits
by tracking request times and enforcing delays when needed.
"""

import time
from typing import List


class RateLimiter:
    """My class for controlling API request rates.

    I set maximum requests allowed in a time window and ensure
    we don't exceed limits by waiting when necessary.
    """

    def __init__(self, max_requests: int, time_window: int) -> None:
        """Initialize rate limiter with request limits.

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
        """Check and wait if rate limit is reached.

        Before making a new request, I check if we've hit the limit.
        If we have, I wait until enough time has passed since the
        oldest request.
        """
        now = time.time()

        self.requests = [
            req_time for req_time in self.requests if now - req_time <= self.time_window
        ]

        if len(self.requests) >= self.max_requests:
            oldest_request = self.requests[0]
            wait_time = oldest_request + self.time_window - now
            if wait_time > 0:
                time.sleep(wait_time)
                now = time.time()

        self.requests.append(now)
