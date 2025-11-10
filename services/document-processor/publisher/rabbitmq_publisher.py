"""
RabbitMQ publisher for document chunks.
"""
import aio_pika
import json
from typing import Dict, Any, List
from shared.exceptions.custom_exceptions import QueueError
from shared.logging.logger import get_logger

logger = get_logger("rabbitmq_publisher")


class RabbitMQPublisher:
    """Publish messages to RabbitMQ."""
    
    def __init__(self):
        """Initialize publisher."""
        self.connection = None
        self.channel = None
        self.exchange = None
        self._connection_url = None
    
    async def connect(self, connection_url: str):
        """
        Connect to RabbitMQ.
        
        Args:
            connection_url: RabbitMQ connection URL
        """
        try:
            self._connection_url = connection_url
            self.connection = await aio_pika.connect_robust(connection_url)
            self.channel = await self.connection.channel()
            
            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                'document_processing',
                aio_pika.ExchangeType.DIRECT,
                durable=True
            )
            
            # Declare queue for chunk processing
            queue = await self.channel.declare_queue(
                'chunks.processing',
                durable=True
            )
            
            # Bind queue to exchange
            await queue.bind(self.exchange, routing_key='chunk')
            
            # Declare dead letter queue
            dlq = await self.channel.declare_queue(
                'chunks.failed',
                durable=True
            )
            
            logger.info("Connected to RabbitMQ")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise QueueError(f"Failed to connect to RabbitMQ: {str(e)}")
    
    async def disconnect(self):
        """Disconnect from RabbitMQ."""
        if self.connection:
            await self.connection.close()
            logger.info("Disconnected from RabbitMQ")
    
    async def publish_chunk(self, chunk_data: Dict[str, Any]):
        """
        Publish a document chunk for vectorization.
        
        Args:
            chunk_data: Chunk data including text and metadata
        """
        try:
            message_body = json.dumps(chunk_data)
            
            message = aio_pika.Message(
                body=message_body.encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type='application/json'
            )
            
            await self.exchange.publish(
                message,
                routing_key='chunk'
            )
            
            logger.debug(f"Published chunk to queue: {chunk_data.get('chunk_index')}")
            
        except Exception as e:
            logger.error(f"Failed to publish chunk: {str(e)}")
            raise QueueError(f"Failed to publish chunk: {str(e)}")
    
    async def publish_chunks(self, chunks: List[Dict[str, Any]], content_id: str):
        """
        Publish multiple chunks.
        
        Args:
            chunks: List of chunk data
            content_id: Content ID for tracking
        """
        try:
            logger.info(f"Publishing {len(chunks)} chunks for content {content_id}")
            
            for chunk in chunks:
                # Add content_id to each chunk
                chunk['content_id'] = content_id
                await self.publish_chunk(chunk)
            
            logger.info(f"Successfully published all chunks for content {content_id}")
            
        except Exception as e:
            logger.error(f"Failed to publish chunks: {str(e)}")
            raise QueueError(f"Failed to publish chunks: {str(e)}")


# Global publisher instance
rabbitmq_publisher = RabbitMQPublisher()


async def get_publisher() -> RabbitMQPublisher:
    """
    Get RabbitMQ publisher instance.
    
    Returns:
        Publisher instance
    """
    return rabbitmq_publisher

