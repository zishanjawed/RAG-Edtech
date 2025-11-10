"""
Token-based chunking strategy for documents.
Preserves document structure while maintaining optimal chunk sizes.
(Legacy implementation - use DoclingChunker for better results)
"""
from typing import List, Dict, Any
import tiktoken
from shared.exceptions.custom_exceptions import ChunkingError
from shared.logging.logger import get_logger

logger = get_logger("token_based_chunker")


class TokenBasedChunker:
    """
    Hybrid document chunking that preserves structure.
    Uses token-based chunking with semantic boundaries.
    """
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        encoding_name: str = "cl100k_base"  # GPT-4 encoding
    ):
        """
        Initialize chunker.
        
        Args:
            chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks in tokens
            encoding_name: Tokenizer encoding name
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding(encoding_name)
    
    def chunk_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        structure: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Chunk document with hybrid strategy.
        
        Args:
            content: Document content (markdown format)
            metadata: Document metadata
            structure: Document structure (headings, sections)
        
        Returns:
            List of chunks with metadata
        
        Raises:
            ChunkingError: If chunking fails
        """
        try:
            logger.info(f"Chunking document with {len(content)} characters")
            
            # Split by sections first
            sections = self._split_by_structure(content, structure)
            
            # Chunk each section
            chunks = []
            for section in sections:
                section_chunks = self._chunk_section(
                    section['content'],
                    section['metadata']
                )
                chunks.extend(section_chunks)
            
            # Add global metadata to all chunks
            for idx, chunk in enumerate(chunks):
                chunk['chunk_index'] = idx
                chunk['total_chunks'] = len(chunks)
                chunk['document_metadata'] = metadata
                chunk['metadata']['chunking_strategy'] = 'token_based'
            
            logger.info(f"Created {len(chunks)} chunks from document")
            
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to chunk document: {str(e)}")
            raise ChunkingError(
                f"Failed to chunk document: {str(e)}"
            )
    
    def _split_by_structure(
        self,
        content: str,
        structure: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Split content by document structure."""
        sections = []
        lines = content.split('\n')
        
        if not structure:
            # No structure, treat as single section
            return [{
                'content': content,
                'metadata': {
                    'section_title': 'Main Content',
                    'section_level': 0
                }
            }]
        
        # Split by headings
        current_section = []
        current_heading = {'title': 'Introduction', 'level': 0}
        
        for line in lines:
            if line.startswith('#'):
                # Save previous section
                if current_section:
                    sections.append({
                        'content': '\n'.join(current_section),
                        'metadata': {
                            'section_title': current_heading['title'],
                            'section_level': current_heading['level']
                        }
                    })
                    current_section = []
                
                # Start new section
                level = len(line.split()[0])
                title = line.replace('#' * level, '').strip()
                current_heading = {'title': title, 'level': level}
            
            current_section.append(line)
        
        # Add last section
        if current_section:
            sections.append({
                'content': '\n'.join(current_section),
                'metadata': {
                    'section_title': current_heading['title'],
                    'section_level': current_heading['level']
                }
            })
        
        return sections
    
    def _chunk_section(
        self,
        content: str,
        section_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Chunk a section into smaller pieces."""
        chunks = []
        
        # Tokenize content
        tokens = self.encoding.encode(content)
        
        # If section fits in one chunk, return it
        if len(tokens) <= self.chunk_size:
            return [{
                'text': content,
                'token_count': len(tokens),
                'metadata': section_metadata
            }]
        
        # Split into overlapping chunks
        start = 0
        while start < len(tokens):
            end = min(start + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            
            # Decode tokens back to text
            chunk_text = self.encoding.decode(chunk_tokens)
            
            chunks.append({
                'text': chunk_text,
                'token_count': len(chunk_tokens),
                'metadata': {
                    **section_metadata,
                    'start_token': start,
                    'end_token': end
                }
            })
            
            # Move start position with overlap
            start += (self.chunk_size - self.chunk_overlap)
        
        return chunks
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count tokens for
        
        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))

