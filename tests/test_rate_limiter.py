"""Test module for rate limiter."""

import time
from typing import List

import pytest

from src.utils.rate_limiter import RateLimiter


@pytest.fixture
def rate_limiter() -> RateLimiter:
    """
    Create RateLimiter instance for testing.

    Returns:
        RateLimiter: Rate limiter class instance
    """
    return RateLimiter(max_requests=2, time_window=1)


def test_rate_limiter_basic(rate_limiter: RateLimiter) -> None:
    """
    Basic rate limiting test.

    Args:
        rate_limiter: RateLimiter fixture'ı
    """

    start_time = time.time()
    rate_limiter.wait_if_needed()
    rate_limiter.wait_if_needed()
    elapsed = time.time() - start_time

    assert elapsed < 1.0, f"First two requests took too long: {elapsed:.2f} seconds"


def test_rate_limiter_throttling(rate_limiter: RateLimiter) -> None:
    """
    Test for request throttling.

    Args:
        rate_limiter: RateLimiter fixture'ı
    """

    for _ in range(rate_limiter.max_requests):
        rate_limiter.wait_if_needed()

    start_time = time.time()
    rate_limiter.wait_if_needed()
    elapsed = time.time() - start_time

    assert elapsed > 0.1, f"Third request waited too short: {elapsed:.2f} seconds"


def test_rate_limiter_window_reset(rate_limiter):
    # Fill up the window
    for _ in range(rate_limiter.max_requests):
        rate_limiter.wait_if_needed()
    
    start_time = time.time()
    # Make one more request that should be delayed
    rate_limiter.wait_if_needed()
    elapsed = time.time() - start_time
    
    # Should have waited due to rate limiting
    assert elapsed > 0.1, f"Request should be delayed when window is full: {elapsed:.2f} seconds"


def test_rate_limiter_continuous_requests(rate_limiter: RateLimiter) -> None:
    """
    Test for continuous requests.

    Args:
        rate_limiter: RateLimiter fixture'ı
    """
    # Make multiple requests
    for _ in range(5):
        rate_limiter.wait_if_needed()
    
    # Should not exceed rate limit
    assert len(rate_limiter.requests) <= rate_limiter.max_requests


def test_rate_limiter_edge_cases() -> None:
    """Test for edge cases."""

    with pytest.raises(ValueError):
        RateLimiter(max_requests=0, time_window=60)

    with pytest.raises(ValueError):
        RateLimiter(max_requests=30, time_window=0)


def test_rate_limiter_high_load(rate_limiter: RateLimiter) -> None:
    """
    Test for high load.

    Args:
        rate_limiter: RateLimiter fixture'ı
    """
    start_time = time.time()
    request_count = 10

    # Make many requests in a row
    for _ in range(request_count):
        rate_limiter.wait_if_needed()

    total_time = time.time() - start_time
    expected_time = (request_count - 2) / 2  # First 2 requests pass immediately

    assert total_time >= expected_time, (
        f"Rate limiting not working under high load: "
        f"{total_time:.2f} < {expected_time:.2f}"
    )


if __name__ == "__main__":
    pytest.main(["-v", __file__])
