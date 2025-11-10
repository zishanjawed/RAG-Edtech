"""
OpenAI embedding generation with batch processing.
"""
from openai import AsyncOpenAI
from typing import List, Dict, Any
from shared.exceptions.custom_exceptions import OpenAIError
from shared.logging.logger import get_logger
from shared.utils.retry import async_retry

logger = get_logger("openai_embedder")


class OpenAIEmbedder:
    """Generate embeddings using OpenAI API."""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-large"):
        """
        Initialize OpenAI embedder.
        
        Args:
            api_key: OpenAI API key
            model: Embedding model name
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.dimension = 3072 if "large" in model else 1536
    
    @async_retry(max_attempts=3, initial_delay=1.0, exceptions=(Exception,))
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector
        
        Raises:
            OpenAIError: If embedding generation fails
        """
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding of dimension {len(embedding)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise OpenAIError(
                f"Failed to generate embedding: {str(e)}",
                details={"model": self.model}
            )
    
    @async_retry(max_attempts=3, initial_delay=1.0, exceptions=(Exception,))
    async def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of texts to embed
            batch_size: Maximum batch size
        
        Returns:
            List of embedding vectors
        
        Raises:
            OpenAIError: If embedding generation fails
        """
        try:
            embeddings = []
            
            # Process in batches
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                logger.info(f"Processing batch {i // batch_size + 1} ({len(batch)} texts)")
                
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
            
            logger.info(f"Generated {len(embeddings)} embeddings")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {str(e)}")
            raise OpenAIError(
                f"Failed to generate batch embeddings: {str(e)}",
                details={"model": self.model, "batch_size": len(texts)}
            )
    
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.dimension

