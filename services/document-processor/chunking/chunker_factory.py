"""
Chunker factory for selecting and initializing chunking strategies.
Supports multiple chunking strategies with fallback mechanisms.
"""
from typing import Optional
import os

from shared.logging.logger import get_logger
from shared.exceptions.custom_exceptions import ChunkingError

logger = get_logger("chunker_factory")


class ChunkerFactory:
    """
    Factory for creating chunkers based on configuration.
    
    Supported strategies:
    - 'docling': Docling's HybridChunker (recommended, default)
    - 'token_based': Legacy token-based chunker
    """
    
    @staticmethod
    def create_chunker(
        strategy: Optional[str] = None,
        max_tokens: int = 512,
        chunk_overlap: int = 50,
        merge_peers: bool = True,
        **kwargs
    ):
        """
        Create a chunker based on the specified strategy.
        
        Args:
            strategy: Chunking strategy ('docling' or 'token_based')
                     If None, uses CHUNKING_STRATEGY env var (default: 'docling')
            max_tokens: Maximum tokens per chunk
            chunk_overlap: Overlap between chunks (for token_based only)
            merge_peers: Merge small adjacent chunks (for docling only)
            **kwargs: Additional strategy-specific parameters
        
        Returns:
            Chunker instance
        
        Raises:
            ChunkingError: If strategy is invalid or initialization fails
        """
        # Get strategy from parameter or environment variable
        if strategy is None:
            strategy = os.getenv('CHUNKING_STRATEGY', 'docling').lower()
        else:
            strategy = strategy.lower()
        
        logger.info(f"Creating chunker with strategy: {strategy}")
        
        # Try to create the requested chunker
        try:
            if strategy == 'docling':
                return ChunkerFactory._create_docling_chunker(
                    max_tokens=max_tokens,
                    merge_peers=merge_peers,
                    **kwargs
                )
            
            elif strategy == 'token_based':
                return ChunkerFactory._create_token_based_chunker(
                    max_tokens=max_tokens,
                    chunk_overlap=chunk_overlap,
                    **kwargs
                )
            
            else:
                logger.error(f"Unknown chunking strategy: {strategy}")
                raise ChunkingError(
                    f"Unknown chunking strategy: {strategy}. "
                    f"Supported strategies: 'docling', 'token_based'"
                )
        
        except Exception as e:
            logger.error(f"Failed to create {strategy} chunker: {str(e)}")
            
            # Fallback to token_based if docling fails
            if strategy == 'docling':
                logger.warning("Falling back to token_based chunker")
                try:
                    return ChunkerFactory._create_token_based_chunker(
                        max_tokens=max_tokens,
                        chunk_overlap=chunk_overlap
                    )
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {str(fallback_error)}")
                    raise ChunkingError(
                        f"Failed to create chunker: {str(e)}"
                    )
            
            raise ChunkingError(f"Failed to create chunker: {str(e)}")
    
    @staticmethod
    def _create_docling_chunker(
        max_tokens: int = 512,
        merge_peers: bool = True,
        tokenizer_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        **kwargs
    ):
        """Create Docling-based chunker."""
        try:
            from chunking.docling_chunker import DoclingChunker
            
            logger.info(
                f"Initializing Docling chunker "
                f"(max_tokens={max_tokens}, merge_peers={merge_peers})"
            )
            
            chunker = DoclingChunker(
                max_tokens=max_tokens,
                merge_peers=merge_peers,
                tokenizer_model=tokenizer_model
            )
            
            logger.info("[OK] Docling chunker created successfully")
            return chunker
            
        except ImportError as e:
            logger.error(f"Docling not available: {str(e)}")
            raise ChunkingError(
                "Docling library not available. "
                "Install with: pip install docling transformers"
            )
        except Exception as e:
            logger.error(f"Failed to create Docling chunker: {str(e)}")
            raise
    
    @staticmethod
    def _create_token_based_chunker(
        max_tokens: int = 512,
        chunk_overlap: int = 50,
        encoding_name: str = "cl100k_base",
        **kwargs
    ):
        """Create token-based chunker."""
        try:
            from chunking.token_based_chunker import TokenBasedChunker
            
            logger.info(
                f"Initializing token-based chunker "
                f"(max_tokens={max_tokens}, overlap={chunk_overlap})"
            )
            
            chunker = TokenBasedChunker(
                chunk_size=max_tokens,
                chunk_overlap=chunk_overlap,
                encoding_name=encoding_name
            )
            
            logger.info("[OK] Token-based chunker created successfully")
            return chunker
            
        except Exception as e:
            logger.error(f"Failed to create token-based chunker: {str(e)}")
            raise


# Convenience function for quick chunker creation
def get_chunker(strategy: Optional[str] = None, **kwargs):
    """
    Get a chunker instance with the specified strategy.
    
    Args:
        strategy: Chunking strategy or None for default
        **kwargs: Additional chunker parameters
    
    Returns:
        Chunker instance
    """
    return ChunkerFactory.create_chunker(strategy=strategy, **kwargs)

