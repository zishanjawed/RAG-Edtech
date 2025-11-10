"""
Redis client with connection pooling, retry logic, and error handling.
"""
import json
from typing import Any, Optional
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import ConnectionError as RedisConnectionError, TimeoutError as RedisTimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from shared.exceptions.custom_exceptions import CacheError
from shared.logging.logger import get_logger

logger = get_logger("redis_client")


class RedisClient:
    """Redis client wrapper with connection management."""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.pool: Optional[ConnectionPool] = None
        self._connection_string: Optional[str] = None
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RedisConnectionError, RedisTimeoutError)),
        reraise=True
    )
    async def connect(self, connection_string: str):
        """
        Connect to Redis with retry logic.
        
        Args:
            connection_string: Redis connection string (e.g., redis://localhost:6379/0)
        """
        try:
            self._connection_string = connection_string
            
            self.pool = ConnectionPool.from_url(
                connection_string,
                max_connections=50,
                decode_responses=True,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            self.client = redis.Redis(connection_pool=self.pool)
            
            # Verify connection
            await self.client.ping()
            
            logger.info("Connected to Redis")
            
        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise CacheError(f"Failed to connect to Redis: {str(e)}")
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.client:
            await self.client.close()
            await self.pool.disconnect()
            logger.info("Disconnected from Redis")
    
    async def health_check(self) -> bool:
        """
        Check if Redis connection is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            await self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return False
    
    async def get(self, key: str) -> Optional[str]:
        """
        Get value from Redis.
        
        Args:
            key: Cache key
        
        Returns:
            Value or None if not found
        """
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Failed to get key {key} from Redis: {str(e)}")
            raise CacheError(f"Failed to get key from Redis: {str(e)}")
    
    async def get_json(self, key: str) -> Optional[Any]:
        """
        Get JSON value from Redis.
        
        Args:
            key: Cache key
        
        Returns:
            Deserialized value or None if not found
        """
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON for key {key}")
                return None
        return None
    
    async def set(self, key: str, value: str, ttl: Optional[int] = None):
        """
        Set value in Redis.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
        """
        try:
            if ttl:
                await self.client.setex(key, ttl, value)
            else:
                await self.client.set(key, value)
        except Exception as e:
            logger.error(f"Failed to set key {key} in Redis: {str(e)}")
            raise CacheError(f"Failed to set key in Redis: {str(e)}")
    
    async def set_json(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set JSON value in Redis.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (optional)
        """
        try:
            json_value = json.dumps(value)
            await self.set(key, json_value, ttl)
        except Exception as e:
            logger.error(f"Failed to set JSON key {key} in Redis: {str(e)}")
            raise CacheError(f"Failed to set JSON key in Redis: {str(e)}")
    
    async def delete(self, key: str):
        """
        Delete key from Redis.
        
        Args:
            key: Cache key
        """
        try:
            await self.client.delete(key)
        except Exception as e:
            logger.error(f"Failed to delete key {key} from Redis: {str(e)}")
            raise CacheError(f"Failed to delete key from Redis: {str(e)}")
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in Redis.
        
        Args:
            key: Cache key
        
        Returns:
            True if exists, False otherwise
        """
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Failed to check existence of key {key} in Redis: {str(e)}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment counter in Redis.
        
        Args:
            key: Cache key
            amount: Amount to increment
        
        Returns:
            New value after increment
        """
        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Failed to increment key {key} in Redis: {str(e)}")
            raise CacheError(f"Failed to increment key in Redis: {str(e)}")
    
    async def expire(self, key: str, ttl: int):
        """
        Set TTL for existing key.
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
        """
        try:
            await self.client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Failed to set expiry for key {key} in Redis: {str(e)}")
            raise CacheError(f"Failed to set expiry in Redis: {str(e)}")


# Global Redis client instance
redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """
    Dependency for FastAPI routes.
    
    Returns:
        Redis client instance
    """
    return redis_client

