import pytest
from main import RateLimiter
import time
from datetime import datetime, timedelta

def test_rate_limiter_basic():
    """Temel rate limiting testi"""
    limiter = RateLimiter(max_requests=2, time_window=1)
    
    # İlk iki istek hemen geçmeli
    start = time.time()
    limiter.wait_if_needed()
    limiter.wait_if_needed()
    elapsed = time.time() - start
    
    assert elapsed < 0.1  # İlk iki istek neredeyse anında geçmeli

def test_rate_limiter_waiting():
    """Bekleme süresi testi"""
    limiter = RateLimiter(max_requests=2, time_window=1)
    
    # İlk iki isteği yap
    limiter.wait_if_needed()
    limiter.wait_if_needed()
    
    # Üçüncü istek için süre ölç
    start = time.time()
    limiter.wait_if_needed()
    elapsed = time.time() - start
    
    assert elapsed >= 1.0  # En az 1 saniye beklemiş olmalı

def test_rate_limiter_cleanup():
    """Eski isteklerin temizlenmesi testi"""
    limiter = RateLimiter(max_requests=2, time_window=1)
    
    # İki istek yap
    limiter.wait_if_needed()
    limiter.wait_if_needed()
    
    # 1 saniye bekle
    time.sleep(1.1)
    
    # Yeni istek yapılabilmeli
    start = time.time()
    limiter.wait_if_needed()
    elapsed = time.time() - start
    
    assert elapsed < 0.1  # Bekleme olmamalı 