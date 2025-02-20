"""Rate limiter sınıfı için test modülü."""

import time
from typing import List

import pytest

from main import RateLimiter


@pytest.fixture
def rate_limiter() -> RateLimiter:
    """
    Test için RateLimiter instance'ı oluştur.

    Returns:
        RateLimiter: Rate limiter sınıfı instance'ı
    """
    return RateLimiter(max_requests=2, time_window=1)


def test_rate_limiter_basic(rate_limiter: RateLimiter) -> None:
    """
    Temel rate limiting testi.

    Args:
        rate_limiter: RateLimiter fixture'ı
    """
    # İlk iki istek hemen geçmeli
    start = time.time()
    rate_limiter.wait_if_needed()
    rate_limiter.wait_if_needed()
    elapsed = time.time() - start
    
    assert elapsed < 0.1, (
        f"İlk iki istek çok uzun sürdü: {elapsed:.2f} saniye"
    )


def test_rate_limiter_throttling(rate_limiter: RateLimiter) -> None:
    """
    İstek kısıtlama testi.

    Args:
        rate_limiter: RateLimiter fixture'ı
    """
    # İlk iki isteği yap
    rate_limiter.wait_if_needed()
    rate_limiter.wait_if_needed()
    
    # Üçüncü istek beklemeli
    start = time.time()
    rate_limiter.wait_if_needed()
    elapsed = time.time() - start
    
    assert elapsed >= 1.0, (
        f"Üçüncü istek yeterince beklemedi: {elapsed:.2f} saniye"
    )


def test_rate_limiter_window_reset(rate_limiter: RateLimiter) -> None:
    """
    Zaman penceresi sıfırlama testi.

    Args:
        rate_limiter: RateLimiter fixture'ı
    """
    # İlk iki isteği yap
    rate_limiter.wait_if_needed()
    rate_limiter.wait_if_needed()
    
    # Zaman penceresinin sıfırlanmasını bekle
    time.sleep(1.1)
    
    # Yeni istek hemen geçmeli
    start = time.time()
    rate_limiter.wait_if_needed()
    elapsed = time.time() - start
    
    assert elapsed < 0.1, (
        f"Pencere sıfırlandıktan sonra istek gecikti: {elapsed:.2f} saniye"
    )


def test_rate_limiter_continuous_requests(rate_limiter: RateLimiter) -> None:
    """
    Sürekli istek testi.

    Args:
        rate_limiter: RateLimiter fixture'ı
    """
    request_times: List[float] = []
    start_time = time.time()
    
    # 5 istek yap ve zamanları kaydet
    for _ in range(5):
        rate_limiter.wait_if_needed()
        request_times.append(time.time() - start_time)
    
    # İstekler arası süreleri kontrol et
    for i in range(2, len(request_times)):
        time_diff = request_times[i] - request_times[i-2]
        assert time_diff >= 1.0, (
            f"İstekler arası süre çok kısa: {time_diff:.2f} saniye"
        )


def test_rate_limiter_edge_cases() -> None:
    """Sınır durumları testi."""
    # Negatif değerlerle başlatma denemesi
    with pytest.raises(ValueError):
        RateLimiter(max_requests=-1, time_window=1)
    
    with pytest.raises(ValueError):
        RateLimiter(max_requests=1, time_window=-1)
    
    # Sıfır değerleriyle başlatma denemesi
    with pytest.raises(ValueError):
        RateLimiter(max_requests=0, time_window=1)
    
    with pytest.raises(ValueError):
        RateLimiter(max_requests=1, time_window=0)


def test_rate_limiter_high_load(rate_limiter: RateLimiter) -> None:
    """
    Yüksek yük testi.

    Args:
        rate_limiter: RateLimiter fixture'ı
    """
    start_time = time.time()
    request_count = 10
    
    # Art arda çok sayıda istek yap
    for _ in range(request_count):
        rate_limiter.wait_if_needed()
    
    total_time = time.time() - start_time
    expected_time = (request_count - 2) / 2  # İlk 2 istek hemen geçer
    
    assert total_time >= expected_time, (
        f"Yüksek yükte rate limiting çalışmıyor: "
        f"{total_time:.2f} < {expected_time:.2f}"
    )


if __name__ == "__main__":
    pytest.main(["-v", __file__]) 