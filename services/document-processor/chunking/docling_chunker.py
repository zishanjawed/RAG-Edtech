"""
Docling-based hybrid chunking strategy.
Wraps Docling's production-grade HybridChunker with intelligent
document structure awareness and token-based refinements.
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import tempfile

from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker as DoclingHybridChunker
from transformers import AutoTokenizer

from shared.exceptions.custom_exceptions import ChunkingError
from shared.logging.logger import get_logger

logger = get_logger("docling_chunker")


class DoclingChunker:
    """
    Docling-based hybrid chunker that respects document structure
    and applies token-aware refinements.
    
    Features:
    - Hierarchical document structure preservation
    - Token-aware chunking within limits
    - Semantic boundary respect (paragraphs, sections)
    - Metadata and context preservation
    - Automatic heading contextualization
    """
    
    def __init__(
        self,
        max_tokens: int = 512,
        merge_peers: bool = True,
        tokenizer_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """
        Initialize Docling chunker.
        
        Args:
            max_tokens: Maximum tokens per chunk (default: 512)
            merge_peers: Whether to merge small adjacent chunks (default: True)
            tokenizer_model: HuggingFace model for tokenization
        """
        self.max_tokens = max_tokens
        self.merge_peers = merge_peers
        self.tokenizer_model = tokenizer_model
        
        try:
            # Initialize tokenizer
            logger.info(f"Initializing tokenizer: {tokenizer_model}")
            self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_model)
            
            # Initialize Docling HybridChunker
            self.chunker = DoclingHybridChunker(
                tokenizer=self.tokenizer,
                max_tokens=max_tokens,
                merge_peers=merge_peers
            )
            
            logger.info(
                f"Docling chunker initialized "
                f"(max_tokens={max_tokens}, merge_peers={merge_peers})"
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize Docling chunker: {str(e)}")
            raise ChunkingError(
                f"Failed to initialize Docling chunker: {str(e)}"
            )
    
    def chunk_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        structure: List[Dict[str, Any]],
        file_path: Optional[str] = None,
        file_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk document using Docling's HybridChunker.
        
        Args:
            content: Document content (may not be used directly)
            metadata: Document metadata
            structure: Document structure (may not be used directly)
            file_path: Path to original document file
            file_type: Type of file (pdf, txt, md, docx)
        
        Returns:
            List of chunks with metadata
        
        Raises:
            ChunkingError: If chunking fails
        """
        try:
            logger.info(f"Chunking document with Docling (file_type={file_type})")
            
            # Convert document using Docling
            dl_doc = self._convert_document(content, file_path, file_type)
            
            # Generate chunks using Docling's HybridChunker
            logger.info("Generating chunks with Docling HybridChunker...")
            chunk_iter = self.chunker.chunk(dl_doc=dl_doc)
            docling_chunks = list(chunk_iter)
            
            logger.info(f"Docling generated {len(docling_chunks)} chunks")
            
            # Convert Docling chunks to our standard format
            chunks = []
            for idx, dl_chunk in enumerate(docling_chunks):
                # Get contextualized text (preserves headings and structure)
                contextualized_text = self.chunker.contextualize(chunk=dl_chunk)
                
                # Get token count
                token_count = len(self.tokenizer.encode(contextualized_text))
                
                # Build chunk in our standard format
                chunk = {
                    'text': contextualized_text,  # Use contextualized version
                    'raw_text': dl_chunk.text,  # Keep raw text as well
                    'token_count': token_count,
                    'chunk_index': idx,
                    'total_chunks': len(docling_chunks),
                    'metadata': {
                        'chunking_strategy': 'docling',
                        'section_title': self._extract_section_title(dl_chunk),
                        'has_context': True,
                        **metadata
                    },
                    'document_metadata': metadata
                }
                
                # Add Docling-specific metadata if available
                if hasattr(dl_chunk, 'meta') and dl_chunk.meta:
                    chunk['metadata']['docling_meta'] = dl_chunk.meta
                
                chunks.append(chunk)
            
            logger.info(
                f"Successfully created {len(chunks)} chunks using Docling "
                f"(avg tokens: {sum(c['token_count'] for c in chunks) / len(chunks):.1f})"
            )
            
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to chunk document with Docling: {str(e)}")
            raise ChunkingError(
                f"Failed to chunk document with Docling: {str(e)}",
                details={
                    'file_type': file_type,
                    'content_length': len(content) if content else 0
                }
            )
    
    def _convert_document(
        self,
        content: str,
        file_path: Optional[str],
        file_type: Optional[str]
    ):
        """
        Convert document to DoclingDocument.
        
        If file_path is provided, use it directly.
        Otherwise, create a temporary file from content.
        """
        try:
            converter = DocumentConverter()
            
            # If we have the original file path, use it
            if file_path and Path(file_path).exists():
                logger.info(f"Converting document from file: {file_path}")
                result = converter.convert(source=file_path)
                return result.document
            
            # Otherwise, create a temporary file from content
            logger.info("Creating temporary file for Docling conversion")
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix=f'.{file_type or "txt"}',
                delete=False,
                encoding='utf-8'
            ) as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name
            
            try:
                result = converter.convert(source=tmp_path)
                return result.document
            finally:
                # Clean up temp file
                Path(tmp_path).unlink(missing_ok=True)
                
        except Exception as e:
            logger.error(f"Failed to convert document: {str(e)}")
            raise ChunkingError(f"Failed to convert document: {str(e)}")
    
    def _extract_section_title(self, chunk) -> str:
        """Extract section title from Docling chunk if available."""
        try:
            # Try to get contextualized text and extract heading
            context_text = self.chunker.contextualize(chunk=chunk)
            lines = context_text.split('\n')
            
            # Look for heading in first few lines
            for line in lines[:3]:
                line = line.strip()
                if line and not line.startswith('#'):
                    return line[:100]  # First non-heading line as title
            
            return "Content"
            
        except Exception:
            return "Content"
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count tokens for
        
        Returns:
            Number of tokens
        """
        try:
            return len(self.tokenizer.encode(text))
        except Exception as e:
            logger.warning(f"Failed to count tokens: {str(e)}")
            # Fallback to rough estimation
            return len(text) // 4

