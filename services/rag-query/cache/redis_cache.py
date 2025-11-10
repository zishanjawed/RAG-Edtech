"""
Redis caching for RAG responses.
"""
import hashlib
import json
from typing import Optional, Dict, Any
from shared.database.redis_client import redis_client
from shared.logging.logger import get_logger

logger = get_logger("redis_cache")


class ResponseCache:
    """Cache RAG responses in Redis."""
    
    def __init__(self, ttl_seconds: int = 3600, frequency_threshold: int = 5):
        """
        Initialize cache.
        
        Args:
            ttl_seconds: Time to live for cached responses
            frequency_threshold: Number of times question must be asked before caching
        """
        self.ttl = ttl_seconds
        self.frequency_threshold = frequency_threshold
    
    def _generate_cache_key(self, content_id: str, question: str) -> str:
        """
        Generate cache key from content ID and question.
        
        Args:
            content_id: Content ID
            question: Question text
        
        Returns:
            Cache key
        """
        # Create hash of question for consistent key (SHA-256 for security)
        question_hash = hashlib.sha256(question.lower().encode()).hexdigest()
        return f"rag_cache:{content_id}:{question_hash}"
    
    def _generate_frequency_key(self, content_id: str, question: str) -> str:
        """
        Generate frequency tracking key.
        
        Args:
            content_id: Content ID
            question: Question text
        
        Returns:
            Frequency key for counting asks
        """
        question_hash = hashlib.sha256(question.lower().encode()).hexdigest()
        return f"rag_frequency:{content_id}:{question_hash}"
    
    async def increment_question_frequency(
        self,
        content_id: str,
        question: str
    ) -> int:
        """
        Increment and return the frequency count for a question.
        
        Args:
            content_id: Content ID
            question: Question text
        
        Returns:
            Current frequency count after increment
        """
        try:
            frequency_key = self._generate_frequency_key(content_id, question)
            
            # Increment counter
            count = await redis_client.increment(frequency_key)
            
            # Set TTL on first increment (24 hours for frequency tracking)
            if count == 1:
                await redis_client.expire(frequency_key, 86400)  # 24 hours
            
            logger.info(f"Question frequency for content {content_id}: {count}")
            return count
            
        except Exception as e:
            logger.error(f"Failed to increment frequency: {str(e)}")
            return 0
    
    async def get_question_frequency(
        self,
        content_id: str,
        question: str
    ) -> int:
        """
        Get current frequency count for a question.
        
        Args:
            content_id: Content ID
            question: Question text
        
        Returns:
            Current frequency count
        """
        try:
            frequency_key = self._generate_frequency_key(content_id, question)
            count = await redis_client.get(frequency_key)
            return int(count) if count else 0
        except Exception as e:
            logger.error(f"Failed to get frequency: {str(e)}")
            return 0
    
    async def should_use_cache(
        self,
        content_id: str,
        question: str
    ) -> bool:
        """
        Determine if cache should be used based on frequency.
        
        Args:
            content_id: Content ID
            question: Question text
        
        Returns:
            True if frequency >= threshold, False otherwise
        """
        frequency = await self.get_question_frequency(content_id, question)
        return frequency >= self.frequency_threshold
    
    async def get_cached_response(
        self,
        content_id: str,
        question: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response if available AND frequency threshold is met.
        
        Args:
            content_id: Content ID
            question: Question text
        
        Returns:
            Cached response or None
        """
        try:
            # Check if we should use cache based on frequency
            if not await self.should_use_cache(content_id, question):
                logger.debug(f"Frequency threshold not met for content {content_id}")
                return None
            
            cache_key = self._generate_cache_key(content_id, question)
            cached = await redis_client.get_json(cache_key)
            
            if cached:
                logger.info(f"Cache hit for content {content_id} (frequency-based)")
                return cached
            
            logger.debug(f"Cache miss for content {content_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached response: {str(e)}")
            return None
    
    async def cache_response(
        self,
        content_id: str,
        question: str,
        response: str,
        metadata: Dict[str, Any]
    ):
        """
        Cache a response ONLY if frequency threshold is met.
        
        Args:
            content_id: Content ID
            question: Question text
            response: Generated response
            metadata: Additional metadata (chunks, tokens, etc.)
        """
        try:
            # Only cache if frequency threshold is met
            if not await self.should_use_cache(content_id, question):
                frequency = await self.get_question_frequency(content_id, question)
                logger.info(
                    f"Not caching response for content {content_id} - "
                    f"frequency {frequency} < threshold {self.frequency_threshold}"
                )
                return
            
            cache_key = self._generate_cache_key(content_id, question)
            
            cache_data = {
                "response": response,
                "metadata": metadata,
                "cached": True
            }
            
            await redis_client.set_json(cache_key, cache_data, self.ttl)
            
            logger.info(f"Cached response for content {content_id} (frequency-based)")
            
        except Exception as e:
            logger.error(f"Failed to cache response: {str(e)}")
    
    async def clear_content_cache(self, content_id: str):
        """
        Clear all cached responses for a content.
        
        Args:
            content_id: Content ID
        """
        try:
            # Pattern matching not implemented in simple version
            # In production, use Redis SCAN with pattern
            logger.info(f"Cache clear requested for content {content_id}")
        except Exception as e:
            logger.error(f"Failed to clear cache: {str(e)}")

