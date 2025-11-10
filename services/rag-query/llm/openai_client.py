"""
OpenAI LLM client with streaming support.
"""
from openai import AsyncOpenAI
from typing import AsyncIterator, Dict, Any
import json
from shared.exceptions.custom_exceptions import OpenAIError
from shared.logging.logger import get_logger
from shared.utils.retry import async_retry

logger = get_logger("openai_client")


class OpenAIClient:
    """OpenAI client for LLM completions with streaming."""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key
            model: Model name
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
    
    @async_retry(max_attempts=3, initial_delay=1.0, exceptions=(Exception,))
    async def generate_completion(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate a completion (non-streaming).
        
        Args:
            messages: Chat messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            Completion response with usage stats
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return {
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model
            }
            
        except Exception as e:
            logger.error(f"Failed to generate completion: {str(e)}")
            raise OpenAIError(f"Failed to generate completion: {str(e)}")
    
    async def generate_completion_stream(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> AsyncIterator[str]:
        """
        Generate a streaming completion.
        
        Args:
            messages: Chat messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Yields:
            Chunks of generated text
        """
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            
        except Exception as e:
            logger.error(f"Failed to generate streaming completion: {str(e)}")
            raise OpenAIError(f"Failed to generate streaming completion: {str(e)}")
    
    @async_retry(max_attempts=3, initial_delay=1.0, exceptions=(Exception,))
    async def generate_embedding(self, text: str, model: str = "text-embedding-3-large") -> list:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            model: Embedding model
        
        Returns:
            Embedding vector
        """
        try:
            response = await self.client.embeddings.create(
                model=model,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise OpenAIError(f"Failed to generate embedding: {str(e)}")

