"""
Semantic search retrieval from Pinecone.
"""
from typing import List, Dict, Any, Optional
from pinecone import Pinecone
from shared.exceptions.custom_exceptions import PineconeError
from shared.logging.logger import get_logger

logger = get_logger("pinecone_retriever")


class PineconeRetriever:
    """Retrieve relevant chunks from Pinecone."""
    
    def __init__(
        self,
        api_key: str,
        environment: str,
        index_name: str,
        top_k: int = 5
    ):
        """
        Initialize retriever.
        
        Args:
            api_key: Pinecone API key
            environment: Pinecone environment (not used in v3, kept for compatibility)
            index_name: Name of the index
            top_k: Number of results to return
        """
        self.api_key = api_key
        self.environment = environment  # Not used in Pinecone v3+
        self.index_name = index_name
        self.top_k = top_k
        self.pc = None
        self.index = None
    
    def connect(self):
        """Connect to Pinecone."""
        try:
            logger.info(f"Connecting to Pinecone index: {self.index_name}")
            self.pc = Pinecone(api_key=self.api_key)
            self.index = self.pc.Index(self.index_name)
            logger.info(f"[OK] Successfully connected to Pinecone index: {self.index_name}")
        except Exception as e:
            logger.error(f"Failed to connect to Pinecone: {str(e)}")
            raise PineconeError(f"Failed to connect to Pinecone: {str(e)}")
    
    async def retrieve(
        self,
        query_embedding: List[float],
        content_id: str,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query_embedding: Query embedding vector
            content_id: Content ID to search within
            top_k: Number of results (overrides default)
        
        Returns:
            List of relevant chunks with scores
        """
        try:
            k = top_k or self.top_k
            
            logger.info(f"Retrieving top {k} chunks for content {content_id}")
            
            # Query Pinecone with namespace filtering
            results = self.index.query(
                vector=query_embedding,
                top_k=k,
                namespace=content_id,  # Use content_id as namespace
                include_metadata=True
            )
            
            chunks = []
            for match in results['matches']:
                chunks.append({
                    'id': match['id'],
                    'score': match['score'],
                    'text': match['metadata'].get('text', ''),
                    'metadata': match['metadata']
                })
            
            logger.info(f"Retrieved {len(chunks)} chunks")
            
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to retrieve chunks: {str(e)}")
            raise PineconeError(
                f"Failed to retrieve chunks: {str(e)}",
                details={"content_id": content_id}
            )
    
    async def search_global(
        self,
        query_vector: List[float],
        content_ids: List[str],
        top_k: int = 10
    ) -> List[Any]:
        """
        Search across multiple documents (global search).
        
        Args:
            query_vector: Query embedding vector
            content_ids: List of content IDs to search across
            top_k: Number of results to return
        
        Returns:
            List of search results with metadata and scores
        """
        try:
            logger.info(f"Global search across {len(content_ids)} documents, top_k={top_k}")
            
            # Query each namespace separately and merge results
            all_results = []
            
            for content_id in content_ids:
                try:
                    namespace_results = self.index.query(
                        vector=query_vector,
                        top_k=top_k // len(content_ids) + 1,  # Distribute across documents
                        namespace=content_id,
                        include_metadata=True
                    )
                    # Pinecone v3 may return a dict-like object; support both dict and object forms
                    matches = (
                        namespace_results['matches']
                        if isinstance(namespace_results, dict) or hasattr(namespace_results, '__getitem__')
                        else getattr(namespace_results, 'matches', [])
                    )
                    for match in matches or []:
                        all_results.append(match)
                except Exception as e:
                    logger.warning(f"Failed to query namespace {content_id}: {e}")
                    continue
            
            # Sort all results by score
            all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            # Take top_k overall
            top_results = all_results[:top_k]
            
            # Format results
            formatted = []
            for match in top_results:
                class SearchResult:
                    def __init__(self, match_dict):
                        self.id = match_dict['id']
                        self.score = match_dict['score']
                        self.metadata = match_dict['metadata']
                
                formatted.append(SearchResult(match))
            
            logger.info(f"Global search returned {len(formatted)} chunks from {len(set(r.metadata.get('content_id') for r in formatted))} documents")
            
            return formatted
            
        except Exception as e:
            logger.error(f"Global search failed: {e}")
            raise PineconeError(f"Global search failed: {e}")

