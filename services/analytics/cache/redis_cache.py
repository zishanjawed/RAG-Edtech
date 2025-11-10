"""
Redis caching for analytics results.
"""
from shared.database.redis_client import redis_client
from shared.logging.logger import get_logger
from typing import Optional, Any

logger = get_logger("analytics_cache")


class AnalyticsCache:
    """Cache analytics results."""
    
    def __init__(self, ttl_seconds: int = 300):
        """
        Initialize cache.
        
        Args:
            ttl_seconds: Time to live (default: 5 minutes)
        """
        self.ttl = ttl_seconds
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cached analytics."""
        try:
            return await redis_client.get_json(f"analytics:{key}")
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any):
        """Cache analytics results."""
        try:
            await redis_client.set_json(f"analytics:{key}", value, self.ttl)
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")

