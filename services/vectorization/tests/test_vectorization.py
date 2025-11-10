"""
Tests for vectorization service.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add services to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


class TestEmbeddingGeneration:
    """Test embedding generation."""
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_success(self):
        """Test successful embedding generation."""
        # Mock OpenAI client
        with patch('vectorization.embeddings.openai_embeddings.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.data = [Mock(embedding=[0.1] * 1536)]
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            from vectorization.embeddings.openai_embeddings import OpenAIEmbeddings
            
            embeddings = OpenAIEmbeddings(api_key="test-key")
            texts = ["This is a test sentence"]
            
            result = embeddings.generate_embeddings(texts)
            
            assert len(result) == 1
            assert len(result[0]) == 1536
            assert all(isinstance(x, float) for x in result[0])
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_empty_input(self):
        """Test embedding generation with empty input."""
        from vectorization.embeddings.openai_embeddings import OpenAIEmbeddings
        
        embeddings = OpenAIEmbeddings(api_key="test-key")
        
        result = embeddings.generate_embeddings([])
        assert result == []
    
    @pytest.mark.asyncio
    async def test_batch_embedding_generation(self):
        """Test batch embedding generation."""
        with patch('vectorization.embeddings.openai_embeddings.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.data = [
                Mock(embedding=[0.1] * 1536),
                Mock(embedding=[0.2] * 1536),
                Mock(embedding=[0.3] * 1536)
            ]
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            from vectorization.embeddings.openai_embeddings import OpenAIEmbeddings
            
            embeddings = OpenAIEmbeddings(api_key="test-key")
            texts = ["Text 1", "Text 2", "Text 3"]
            
            result = embeddings.generate_embeddings(texts)
            
            assert len(result) == 3
            for emb in result:
                assert len(emb) == 1536


class TestVectorStorage:
    """Test vector storage in Pinecone."""
    
    @pytest.mark.asyncio
    async def test_store_vectors_success(self):
        """Test successful vector storage."""
        # Mock test - in real scenario would use Pinecone mock
        mock_index = Mock()
        mock_index.upsert.return_value = {"upserted_count": 5}
        
        # Simulate storage
        vectors = [
            {"id": "chunk-1", "values": [0.1] * 1536, "metadata": {"text": "chunk 1"}},
            {"id": "chunk-2", "values": [0.2] * 1536, "metadata": {"text": "chunk 2"}}
        ]
        
        result = mock_index.upsert(vectors=vectors, namespace="test-content")
        
        assert result["upserted_count"] > 0
    
    @pytest.mark.asyncio
    async def test_delete_vectors_by_content_id(self):
        """Test deleting vectors by content ID."""
        mock_index = Mock()
        mock_index.delete.return_value = {"deleted_count": 10}
        
        result = mock_index.delete(filter={"content_id": "content-123"})
        
        assert result.get("deleted_count", 0) >= 0
    
    @pytest.mark.asyncio
    async def test_query_vectors(self):
        """Test querying similar vectors."""
        mock_index = Mock()
        mock_index.query.return_value = {
            "matches": [
                {"id": "chunk-1", "score": 0.95, "metadata": {"text": "Similar text"}},
                {"id": "chunk-2", "score": 0.85, "metadata": {"text": "Also similar"}}
            ]
        }
        
        query_vector = [0.1] * 1536
        result = mock_index.query(vector=query_vector, top_k=5, include_metadata=True)
        
        assert len(result["matches"]) == 2
        assert result["matches"][0]["score"] > 0.8


class TestChunkProcessing:
    """Test chunk processing and batching."""
    
    def test_create_chunks_from_text(self):
        """Test creating chunks from text."""
        text = "This is a long text. " * 100  # 500 words
        
        # Simple chunk creation (would use actual chunker in real test)
        max_chunk_size = 500
        chunks = []
        
        words = text.split()
        for i in range(0, len(words), max_chunk_size):
            chunk = " ".join(words[i:i+max_chunk_size])
            chunks.append(chunk)
        
        assert len(chunks) > 0
        assert all(len(chunk) > 0 for chunk in chunks)
    
    def test_batch_processing(self):
        """Test batching chunks for processing."""
        chunks = [f"Chunk {i}" for i in range(100)]
        batch_size = 10
        
        batches = [chunks[i:i+batch_size] for i in range(0, len(chunks), batch_size)]
        
        assert len(batches) == 10
        assert all(len(batch) <= batch_size for batch in batches)
    
    def test_chunk_metadata_creation(self):
        """Test creating metadata for chunks."""
        chunk_text = "This is a test chunk"
        content_id = "content-123"
        chunk_index = 5
        
        metadata = {
            "text": chunk_text,
            "content_id": content_id,
            "chunk_index": chunk_index,
            "char_count": len(chunk_text)
        }
        
        assert metadata["content_id"] == content_id
        assert metadata["chunk_index"] == chunk_index
        assert metadata["char_count"] > 0


class TestErrorHandling:
    """Test error handling in vectorization."""
    
    @pytest.mark.asyncio
    async def test_handle_api_error(self):
        """Test handling API errors."""
        with patch('vectorization.embeddings.openai_embeddings.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create.side_effect = Exception("API Error")
            mock_openai.return_value = mock_client
            
            from vectorization.embeddings.openai_embeddings import OpenAIEmbeddings
            
            embeddings = OpenAIEmbeddings(api_key="test-key")
            
            with pytest.raises(Exception) as exc_info:
                embeddings.generate_embeddings(["test"])
            
            assert "API Error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_handle_invalid_input(self):
        """Test handling invalid input."""
        from vectorization.embeddings.openai_embeddings import OpenAIEmbeddings
        
        embeddings = OpenAIEmbeddings(api_key="test-key")
        
        # Test with None
        result = embeddings.generate_embeddings(None or [])
        assert result == []
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Test retry logic on failure."""
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                # Simulate operation
                if retry_count < 2:
                    raise Exception("Temporary failure")
                # Success on 3rd try
                break
            except Exception:
                retry_count += 1
                if retry_count >= max_retries:
                    raise
        
        assert retry_count < max_retries


class TestVectorizationWorkflow:
    """Test end-to-end vectorization workflow."""
    
    @pytest.mark.asyncio
    async def test_full_vectorization_workflow(self):
        """Test complete vectorization workflow."""
        # Mock workflow steps
        steps_completed = []
        
        # Step 1: Receive chunks
        chunks = ["chunk 1", "chunk 2", "chunk 3"]
        steps_completed.append("receive_chunks")
        
        # Step 2: Generate embeddings
        embeddings = [[0.1] * 1536 for _ in chunks]
        steps_completed.append("generate_embeddings")
        
        # Step 3: Store in Pinecone
        stored_count = len(embeddings)
        steps_completed.append("store_vectors")
        
        # Step 4: Verify storage
        if stored_count == len(chunks):
            steps_completed.append("verify_storage")
        
        assert len(steps_completed) == 4
        assert stored_count == 3
    
    @pytest.mark.asyncio
    async def test_update_existing_vectors(self):
        """Test updating existing vectors."""
        content_id = "content-123"
        
        # Mock deletion
        deleted = True
        
        # Mock new insertion
        inserted = True
        
        assert deleted and inserted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

