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
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize cache.
        
        Args:
            ttl_seconds: Time to live for cached responses
        """
        self.ttl = ttl_seconds
    
    def _generate_cache_key(self, content_id: str, question: str) -> str:
        """
        Generate cache key from content ID and question.
        
        Args:
            content_id: Content ID
            question: Question text
        
        Returns:
            Cache key
        """
        # Create hash of question for consistent key
        question_hash = hashlib.md5(question.lower().encode()).hexdigest()
        return f"rag_cache:{content_id}:{question_hash}"
    
    async def get_cached_response(
        self,
        content_id: str,
        question: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response if available.
        
        Args:
            content_id: Content ID
            question: Question text
        
        Returns:
            Cached response or None
        """
        try:
            cache_key = self._generate_cache_key(content_id, question)
            
            cached = await redis_client.get_json(cache_key)
            
            if cached:
                logger.info(f"Cache hit for content {content_id}")
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
        Cache a response.
        
        Args:
            content_id: Content ID
            question: Question text
            response: Generated response
            metadata: Additional metadata (chunks, tokens, etc.)
        """
        try:
            cache_key = self._generate_cache_key(content_id, question)
            
            cache_data = {
                "response": response,
                "metadata": metadata,
                "cached": True
            }
            
            await redis_client.set_json(cache_key, cache_data, self.ttl)
            
            logger.info(f"Cached response for content {content_id}")
            
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

