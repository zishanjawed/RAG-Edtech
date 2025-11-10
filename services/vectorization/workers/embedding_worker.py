"""
RabbitMQ consumer worker for processing document chunks.
"""
import aio_pika
import json
import asyncio
from typing import Dict, Any
from embeddings.openai_embedder import OpenAIEmbedder
from vector_store.pinecone_client import PineconeClient
from shared.database.mongodb_client import mongodb_client
from shared.database.redis_client import redis_client
from shared.observability.langfuse_client import langfuse_client
from shared.exceptions.custom_exceptions import QueueError
from shared.logging.logger import get_logger

logger = get_logger("embedding_worker")


class EmbeddingWorker:
    """Worker that processes chunks from RabbitMQ queue."""
    
    def __init__(
        self,
        embedder: OpenAIEmbedder,
        pinecone_client: PineconeClient
    ):
        """
        Initialize worker.
        
        Args:
            embedder: OpenAI embedder instance
            pinecone_client: Pinecone client instance
        """
        self.embedder = embedder
        self.pinecone_client = pinecone_client
        self.connection = None
        self.channel = None
        self.queue = None
        self._running = False
    
    async def connect(self, connection_url: str):
        """
        Connect to RabbitMQ.
        
        Args:
            connection_url: RabbitMQ connection URL
        """
        try:
            self.connection = await aio_pika.connect_robust(connection_url)
            self.channel = await self.connection.channel()
            
            # Set prefetch count (process one message at a time per worker)
            await self.channel.set_qos(prefetch_count=10)
            
            # Get queue
            self.queue = await self.channel.get_queue('chunks.processing')
            
            logger.info("Worker connected to RabbitMQ")
            
        except Exception as e:
            logger.error(f"Failed to connect worker to RabbitMQ: {str(e)}")
            raise QueueError(f"Failed to connect to RabbitMQ: {str(e)}")
    
    async def start(self):
        """Start consuming messages from queue."""
        if not self.queue:
            raise QueueError("Worker not connected to queue")
        
        logger.info("Starting embedding worker...")
        self._running = True
        
        await self.queue.consume(self._process_message)
        
        logger.info("Worker started and listening for chunks")
    
    async def stop(self):
        """Stop worker."""
        self._running = False
        if self.connection:
            await self.connection.close()
        logger.info("Worker stopped")
    
    async def _process_message(self, message: aio_pika.IncomingMessage):
        """
        Process a single message from queue.
        
        Args:
            message: Incoming message with chunk data
        """
        async with message.process():
            try:
                # Parse message
                chunk_data = json.loads(message.body.decode())
                
                content_id = chunk_data.get('content_id')
                chunk_index = chunk_data.get('chunk_index')
                text = chunk_data.get('text')
                
                logger.info(f"Processing chunk {chunk_index} for content {content_id}")
                
                # Start trace
                trace = None
                if langfuse_client.is_enabled():
                    trace = langfuse_client.trace(
                        name="vectorization",
                        metadata={
                            "content_id": content_id,
                            "chunk_index": chunk_index
                        }
                    )
                
                # Generate embedding
                if langfuse_client.is_enabled():
                    langfuse_client.span(
                        name="generate_embedding",
                        input={"text_length": len(text)},
                        trace_id=trace.id if trace else None
                    )
                
                embedding = await self.embedder.generate_embedding(text)
                
                # Prepare metadata for Pinecone
                metadata = {
                    "content_id": content_id,
                    "chunk_index": chunk_index,
                    "text": text[:40000],  # Pinecone metadata limit
                    "token_count": chunk_data.get('token_count', 0),
                    **chunk_data.get('metadata', {})
                }
                
                # Store in Pinecone
                if langfuse_client.is_enabled():
                    langfuse_client.span(
                        name="store_vector",
                        input={"content_id": content_id, "chunk_index": chunk_index},
                        trace_id=trace.id if trace else None
                    )
                
                vector_id = f"{content_id}_{chunk_index}"
                namespace = content_id  # Use content_id as namespace for isolation
                
                await self.pinecone_client.upsert_vector(
                    vector_id=vector_id,
                    vector=embedding,
                    metadata=metadata,
                    namespace=namespace
                )
                
                # Update MongoDB progress atomically and check completion in one operation
                db = mongodb_client.get_database()
                # Use find_one_and_update to atomically increment and return updated document
                updated_doc = await db.content.find_one_and_update(
                    {"content_id": content_id},
                    {"$inc": {"processed_chunks": 1}},
                    return_document=True  # Return updated document
                )
                
                # Publish progress updates periodically
                if updated_doc:
                    processed = updated_doc.get('processed_chunks', 0)
                    total = updated_doc.get('total_chunks', 0)
                    
                    # Publish every 5 chunks or on completion for real-time feedback
                    if processed % 5 == 0 or processed >= total:
                        try:
                            progress = int((processed / total) * 100) if total > 0 else 0
                            status_update = {
                                "status": "processing" if processed < total else "completed",
                                "progress": progress,
                                "message": f"Vectorizing... {processed}/{total} chunks",
                                "processed_chunks": processed,
                                "total_chunks": total
                            }
                            
                            channel = f"document:status:{content_id}"
                            await redis_client.client.publish(channel, json.dumps(status_update))
                            logger.debug(f"Published progress to Redis: {channel} - {progress}%")
                        except Exception as e:
                            logger.warning(f"Failed to publish progress: {e}")
                
                # Check if all chunks are processed using the updated document
                if updated_doc:
                    processed = updated_doc.get('processed_chunks', 0)
                    total = updated_doc.get('total_chunks', 0)
                    if processed >= total and updated_doc.get('status') != 'completed':
                        # Mark as completed atomically
                        await db.content.update_one(
                            {"content_id": content_id, "status": {"$ne": "completed"}},
                            {"$set": {"status": "completed"}}
                        )
                        logger.info(f"Content {content_id} processing completed ({processed}/{total} chunks)")
                        
                        # Publish completion status to Redis for WebSocket clients
                        try:
                            status_update = {
                                "status": "completed",
                                "progress": 100,
                                "message": "Document ready for chat!",
                                "processed_chunks": processed,
                                "total_chunks": total
                            }
                            
                            channel = f"document:status:{content_id}"
                            await redis_client.client.publish(channel, json.dumps(status_update))
                            logger.info(f"Published completion to Redis: {channel}")
                        except Exception as e:
                            logger.error(f"Failed to publish status to Redis: {e}", exc_info=True)
                
                logger.info(f"Successfully processed chunk {chunk_index} for content {content_id}")
                
                # Flush Langfuse
                if langfuse_client.is_enabled():
                    langfuse_client.flush()
                
            except Exception as e:
                logger.error(f"Failed to process chunk: {str(e)}")
                
                # Send to dead letter queue on failure
                # The message will be rejected and moved to DLQ automatically
                raise

