"""
Unit tests for Document Processing Service.
"""
import pytest
from chunking.hybrid_chunker import HybridChunker


@pytest.fixture
def chunker():
    """Create HybridChunker instance."""
    return HybridChunker(chunk_size=512, chunk_overlap=50)


def test_token_counting(chunker):
    """Test 1: Token counting functionality."""
    text = "This is a test sentence for token counting."
    token_count = chunker.count_tokens(text)
    
    # Should have some tokens
    assert token_count > 0
    assert token_count < len(text)  # Tokens should be less than characters


def test_chunk_creation(chunker):
    """Test 2: Document chunking creates proper chunks."""
    # Create sample content
    content = """
# Introduction

This is the introduction section. It contains important information about covalent bonding.

## Molecular Structure

Molecules are formed through covalent bonds. This section explains the structure.

### Bond Types

There are different types of covalent bonds including single, double, and triple bonds.
""" * 5  # Repeat to make it large enough to chunk
    
    metadata = {"title": "Test Document"}
    structure = [
        {"type": "heading", "level": 1, "title": "Introduction"},
        {"type": "heading", "level": 2, "title": "Molecular Structure"}
    ]
    
    chunks = chunker.chunk_document(content, metadata, structure)
    
    # Should create multiple chunks
    assert len(chunks) > 0
    
    # Each chunk should have required fields
    for chunk in chunks:
        assert 'text' in chunk
        assert 'token_count' in chunk
        assert 'chunk_index' in chunk
        assert 'metadata' in chunk
        assert chunk['token_count'] <= 512 + 50  # Allow for overlap


def test_chunk_overlap(chunker):
    """Test 3: Chunks should have proper overlap."""
    # Create long content
    content = " ".join([f"Sentence {i} with some content." for i in range(200)])
    
    metadata = {}
    structure = []
    
    chunks = chunker.chunk_document(content, metadata, structure)
    
    # Should have multiple chunks
    assert len(chunks) > 1
    
    # Check that chunk indices are sequential
    for i, chunk in enumerate(chunks):
        assert chunk['chunk_index'] == i


def test_small_document_single_chunk(chunker):
    """Test 4: Small documents should create single chunk."""
    content = "This is a short document that fits in one chunk."
    metadata = {}
    structure = []
    
    chunks = chunker.chunk_document(content, metadata, structure)
    
    # Should create only one chunk
    assert len(chunks) == 1
    assert chunks[0]['text'] == content

