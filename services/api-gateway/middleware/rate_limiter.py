"""
Rate limiting middleware using Redis.
"""
from fastapi import Request, HTTPException, status
from typing import Optional
import time
from shared.database.redis_client import redis_client
from shared.exceptions.custom_exceptions import RateLimitError
from shared.logging.logger import get_logger

logger = get_logger("rate_limiter")


class RateLimiter:
    """Rate limiter using Redis sliding window."""
    
    def __init__(
        self,
        requests_per_window: int,
        window_seconds: int
    ):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_window: Maximum requests allowed in window
            window_seconds: Time window in seconds
        """
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
    
    async def check_rate_limit(
        self,
        key: str,
        identifier: str
    ) -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            key: Rate limit key (e.g., "rate_limit:user:{user_id}")
            identifier: Identifier for logging
        
        Returns:
            True if within limit, raises RateLimitError otherwise
        """
        try:
            current_time = time.time()
            window_start = current_time - self.window_seconds
            
            # Remove old entries
            await redis_client.client.zremrangebyscore(key, 0, window_start)
            
            # Count requests in current window
            request_count = await redis_client.client.zcard(key)
            
            if request_count >= self.requests_per_window:
                logger.warning(
                    f"Rate limit exceeded for {identifier}",
                    extra={"key": key, "count": request_count}
                )
                raise RateLimitError(
                    f"Rate limit exceeded. Maximum {self.requests_per_window} requests per {self.window_seconds // 3600} hour(s).",
                    details={
                        "limit": self.requests_per_window,
                        "window_seconds": self.window_seconds,
                        "current_count": request_count
                    }
                )
            
            # Add current request
            await redis_client.client.zadd(
                key,
                {str(current_time): current_time}
            )
            
            # Set expiry
            await redis_client.expire(key, self.window_seconds)
            
            return True
            
        except RateLimitError:
            raise
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            # Fail closed for security - deny request if Redis fails
            raise RateLimitError(
                "Rate limiting service unavailable. Please try again later.",
                details={"error": str(e)}
            )


async def check_user_rate_limit(
    user_id: str,
    rate_limit_per_user: int,
    rate_limit_window_hours: int
):
    """
    Check rate limit for a specific user.
    
    Args:
        user_id: User identifier
        rate_limit_per_user: Max requests per user
        rate_limit_window_hours: Window in hours
    """
    rate_limiter = RateLimiter(
        requests_per_window=rate_limit_per_user,
        window_seconds=rate_limit_window_hours * 3600
    )
    
    key = f"rate_limit:user:{user_id}"
    await rate_limiter.check_rate_limit(key, f"user {user_id}")


async def check_global_rate_limit(
    rate_limit_global: int,
    rate_limit_window_hours: int
):
    """
    Check global rate limit.
    
    Args:
        rate_limit_global: Max requests globally
        rate_limit_window_hours: Window in hours
    """
    rate_limiter = RateLimiter(
        requests_per_window=rate_limit_global,
        window_seconds=rate_limit_window_hours * 3600
    )
    
    key = "rate_limit:global"
    await rate_limiter.check_rate_limit(key, "global")

