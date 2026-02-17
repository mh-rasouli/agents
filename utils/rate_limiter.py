"""Rate limiter for API calls to prevent throttling."""

import time
from threading import Lock
from typing import Callable, Any
from functools import wraps

from utils.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Thread-safe rate limiter using token bucket algorithm.

    Prevents API rate limit errors by controlling the rate of API calls.
    """

    def __init__(self, calls_per_minute: int = 60, burst_size: int = 10):
        """Initialize the rate limiter.

        Args:
            calls_per_minute: Maximum calls allowed per minute
            burst_size: Maximum burst size (number of immediate calls allowed)
        """
        self.calls_per_minute = calls_per_minute
        self.interval = 60.0 / calls_per_minute  # Seconds between calls
        self.burst_size = burst_size

        # Token bucket
        self.tokens = float(burst_size)
        self.max_tokens = float(burst_size)
        self.last_update = time.time()

        # Thread safety
        self.lock = Lock()

        # Statistics
        self.total_calls = 0
        self.total_wait_time = 0.0

    def acquire(self) -> float:
        """Acquire permission to make an API call.

        Blocks if necessary to maintain rate limit.

        Returns:
            Time waited in seconds
        """
        with self.lock:
            now = time.time()

            # Add new tokens based on time elapsed
            time_passed = now - self.last_update
            self.tokens = min(self.max_tokens, self.tokens + time_passed / self.interval)
            self.last_update = now

            # If no tokens available, wait
            wait_time = 0.0
            if self.tokens < 1.0:
                wait_time = (1.0 - self.tokens) * self.interval
                time.sleep(wait_time)
                self.tokens = 1.0
                self.last_update = time.time()

            # Consume one token
            self.tokens -= 1.0

            # Update statistics
            self.total_calls += 1
            self.total_wait_time += wait_time

            return wait_time

    def __call__(self, func: Callable) -> Callable:
        """Decorator to rate-limit a function.

        Args:
            func: Function to rate-limit

        Returns:
            Wrapped function with rate limiting
        """
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            wait_time = self.acquire()
            if wait_time > 0:
                logger.debug(f"Rate limited {func.__name__}: waited {wait_time:.2f}s")
            return func(*args, **kwargs)
        return wrapper

    def get_stats(self) -> dict:
        """Get rate limiter statistics.

        Returns:
            Dictionary with statistics
        """
        with self.lock:
            return {
                "total_calls": self.total_calls,
                "total_wait_time": self.total_wait_time,
                "avg_wait_time": self.total_wait_time / self.total_calls if self.total_calls > 0 else 0,
                "current_tokens": self.tokens,
                "max_tokens": self.max_tokens
            }

    def reset_stats(self):
        """Reset statistics."""
        with self.lock:
            self.total_calls = 0
            self.total_wait_time = 0.0


# Global rate limiters for different APIs
openrouter_limiter = RateLimiter(calls_per_minute=60, burst_size=10)
tavily_limiter = RateLimiter(calls_per_minute=100, burst_size=20)
sheets_limiter = RateLimiter(calls_per_minute=100, burst_size=20)
