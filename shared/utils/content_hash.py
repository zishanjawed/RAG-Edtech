"""
Content hashing utilities for document deduplication.

Uses SHA-256 hashing to detect duplicate documents based on content.
"""
import hashlib
import re
from typing import Optional
from shared.logging.logger import get_logger

logger = get_logger("content_hash")


class ContentHasher:
    """Generate content hashes for document deduplication."""
    
    @staticmethod
    def normalize_content(content: str) -> str:
        """
        Normalize content before hashing to improve duplicate detection.
        
        Args:
            content: Raw text content
        
        Returns:
            Normalized content
        """
        # Convert to lowercase
        normalized = content.lower()
        
        # Normalize whitespace (multiple spaces/newlines to single space)
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Strip leading/trailing whitespace
        normalized = normalized.strip()
        
        return normalized
    
    @staticmethod
    def generate_content_hash(content: str, normalize: bool = True) -> str:
        """
        Generate SHA-256 hash of document content.
        
        Args:
            content: Document text content
            normalize: Whether to normalize content before hashing
        
        Returns:
            Hexadecimal hash string (64 characters)
        """
        if not content:
            logger.warning("Empty content provided for hashing")
            return hashlib.sha256(b"").hexdigest()
        
        # Normalize content if requested
        if normalize:
            content = ContentHasher.normalize_content(content)
        
        # Generate SHA-256 hash
        hash_obj = hashlib.sha256(content.encode('utf-8'))
        content_hash = hash_obj.hexdigest()
        
        logger.debug(f"Generated content hash: {content_hash[:16]}... (length: {len(content)})")
        
        return content_hash
    
    @staticmethod
    def verify_content_hash(content: str, expected_hash: str, normalize: bool = True) -> bool:
        """
        Verify if content matches expected hash.
        
        Args:
            content: Document text content
            expected_hash: Expected hash to verify against
            normalize: Whether to normalize content before hashing
        
        Returns:
            True if hashes match, False otherwise
        """
        actual_hash = ContentHasher.generate_content_hash(content, normalize)
        return actual_hash == expected_hash
    
    @staticmethod
    def generate_file_hash(file_path: str) -> Optional[str]:
        """
        Generate hash of a file without loading entire content into memory.
        
        Args:
            file_path: Path to file
        
        Returns:
            Hexadecimal hash string or None if file doesn't exist
        """
        try:
            hash_obj = hashlib.sha256()
            
            with open(file_path, 'rb') as f:
                # Read file in chunks to handle large files
                while chunk := f.read(8192):
                    hash_obj.update(chunk)
            
            file_hash = hash_obj.hexdigest()
            logger.debug(f"Generated file hash for {file_path}: {file_hash[:16]}...")
            
            return file_hash
            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Failed to generate file hash: {e}")
            return None


# Global instance
content_hasher = ContentHasher()

