"""
Pinecone vector store client for storing and querying embeddings.
"""
from pinecone import Pinecone
from typing import List, Dict, Any, Optional
import time
from shared.exceptions.custom_exceptions import PineconeError
from shared.logging.logger import get_logger
from shared.utils.retry import async_retry

logger = get_logger("pinecone_client")


class PineconeClient:
    """Pinecone vector database client."""
    
    def __init__(
        self,
        api_key: str,
        environment: str,
        index_name: str,
        dimension: int = 3072
    ):
        """
        Initialize Pinecone client.
        
        Args:
            api_key: Pinecone API key
            environment: Pinecone environment (not used in v3, kept for compatibility)
            index_name: Name of the index
            dimension: Vector dimension
        """
        self.api_key = api_key
        self.environment = environment  # Not used in Pinecone v3+
        self.index_name = index_name
        self.dimension = dimension
        self.pc = None
        self.index = None
    
    def connect(self):
        """Connect to Pinecone and initialize index."""
        try:
            logger.info(f"Connecting to Pinecone with API key...")
            
            # Initialize Pinecone client (v3+ API - works with serverless)
            self.pc = Pinecone(api_key=self.api_key)
            
            # List all indexes
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            logger.info(f"Found existing indexes: {existing_indexes}")
            
            if self.index_name not in existing_indexes:
                error_msg = (
                    f"Index '{self.index_name}' not found. "
                    f"Available indexes: {existing_indexes}\n"
                    f"Please create a serverless index in the Pinecone dashboard with:\n"
                    f"  - Name: {self.index_name}\n"
                    f"  - Dimensions: {self.dimension}\n"
                    f"  - Metric: cosine\n"
                    f"  - Model: text-embedding-3-large"
                )
                logger.error(error_msg)
                raise PineconeError(error_msg)
            
            # Connect to existing index (supports both serverless and pod-based)
            self.index = self.pc.Index(self.index_name)
            
            logger.info(f"[OK] Successfully connected to Pinecone index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Pinecone: {str(e)}")
            raise PineconeError(
                f"Failed to connect to Pinecone: {str(e)}",
                details={"index_name": self.index_name}
            )
    
    async def upsert_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Dict[str, Any],
        namespace: Optional[str] = None
    ):
        """
        Upsert a single vector.
        
        Args:
            vector_id: Unique vector ID
            vector: Embedding vector
            metadata: Metadata to store with vector
            namespace: Optional namespace for isolation
        """
        try:
            self.index.upsert(
                vectors=[(vector_id, vector, metadata)],
                namespace=namespace or ""
            )
            
            logger.debug(f"Upserted vector {vector_id}")
            
        except Exception as e:
            logger.error(f"Failed to upsert vector: {str(e)}")
            raise PineconeError(
                f"Failed to upsert vector: {str(e)}",
                details={"vector_id": vector_id}
            )
    
    async def upsert_vectors_batch(
        self,
        vectors: List[tuple],
        namespace: Optional[str] = None,
        batch_size: int = 100
    ):
        """
        Upsert multiple vectors in batches.
        
        Args:
            vectors: List of (id, vector, metadata) tuples
            namespace: Optional namespace for isolation
            batch_size: Batch size for upserting
        """
        try:
            logger.info(f"Upserting {len(vectors)} vectors")
            
            # Process in batches
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                
                self.index.upsert(
                    vectors=batch,
                    namespace=namespace or ""
                )
                
                logger.debug(f"Upserted batch {i // batch_size + 1}")
            
            logger.info(f"Successfully upserted all {len(vectors)} vectors")
            
        except Exception as e:
            logger.error(f"Failed to upsert vectors batch: {str(e)}")
            raise PineconeError(
                f"Failed to upsert vectors batch: {str(e)}",
                details={"batch_count": len(vectors)}
            )
    
    async def query_vectors(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Query similar vectors.
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filter_dict: Optional metadata filter
            namespace: Optional namespace
            include_metadata: Include metadata in results
        
        Returns:
            List of matches with scores and metadata
        """
        try:
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                filter=filter_dict,
                namespace=namespace or "",
                include_metadata=include_metadata
            )
            
            matches = []
            for match in results['matches']:
                matches.append({
                    'id': match['id'],
                    'score': match['score'],
                    'metadata': match.get('metadata', {})
                })
            
            logger.debug(f"Found {len(matches)} matches")
            
            return matches
            
        except Exception as e:
            logger.error(f"Failed to query vectors: {str(e)}")
            raise PineconeError(
                f"Failed to query vectors: {str(e)}",
                details={"top_k": top_k}
            )
    
    def get_index_stats(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Get index statistics.
        
        Args:
            namespace: Optional namespace
        
        Returns:
            Index statistics
        """
        try:
            stats = self.index.describe_index_stats()
            return stats
        except Exception as e:
            logger.error(f"Failed to get index stats: {str(e)}")
            return {}
    
    def delete_namespace(self, namespace: str):
        """
        Delete all vectors in a namespace.
        
        Args:
            namespace: Namespace to delete
        """
        try:
            self.index.delete(delete_all=True, namespace=namespace)
            logger.info(f"Deleted namespace: {namespace}")
        except Exception as e:
            logger.error(f"Failed to delete namespace: {str(e)}")
            raise PineconeError(
                f"Failed to delete namespace: {str(e)}",
                details={"namespace": namespace}
            )

