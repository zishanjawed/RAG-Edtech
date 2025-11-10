"""
Vectorization Service - Generates embeddings and stores in Pinecone.
Consumes chunks from RabbitMQ queue.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from embeddings.openai_embedder import OpenAIEmbedder
from vector_store.pinecone_client import PineconeClient
from workers.embedding_worker import EmbeddingWorker
from config import settings
from shared.database.mongodb_client import mongodb_client
from shared.observability.langfuse_client import langfuse_client
from shared.middleware.error_handler import register_exception_handlers
from shared.logging.logger import get_logger

logger = get_logger(settings.service_name, settings.log_level)

# Create FastAPI app
app = FastAPI(
    title="RAG Edtech - Vectorization Service",
    description="Embedding generation and vector storage service",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
register_exception_handlers(app)

# Initialize components
embedder = None
pinecone_client = None
worker = None
worker_task = None


@app.on_event("startup")
async def startup_event():
    """Initialize connections and start worker on startup."""
    global embedder, pinecone_client, worker, worker_task
    
    logger.info("Starting Vectorization Service...")
    
    # Connect to MongoDB
    await mongodb_client.connect(
        settings.mongodb_url,
        settings.mongodb_database
    )
    
    # Initialize OpenAI embedder
    if settings.openai_api_key:
        embedder = OpenAIEmbedder(
            api_key=settings.openai_api_key,
            model=settings.embedding_model
        )
        logger.info(f"Initialized OpenAI embedder with model {settings.embedding_model}")
    else:
        logger.error("OpenAI API key not provided!")
        raise ValueError("OPENAI_API_KEY is required")
    
    # Initialize Pinecone client
    if settings.pinecone_api_key and settings.pinecone_environment:
        pinecone_client = PineconeClient(
            api_key=settings.pinecone_api_key,
            environment=settings.pinecone_environment,
            index_name=settings.pinecone_index_name,
            dimension=embedder.get_dimension()
        )
        pinecone_client.connect()
        logger.info(f"Connected to Pinecone index {settings.pinecone_index_name}")
    else:
        logger.error("Pinecone credentials not provided!")
        raise ValueError("PINECONE_API_KEY and PINECONE_ENVIRONMENT are required")
    
    # Initialize Langfuse
    if settings.langfuse_public_key and settings.langfuse_secret_key:
        langfuse_client.initialize(
            settings.langfuse_public_key,
            settings.langfuse_secret_key,
            settings.langfuse_host
        )
    
    # Initialize and start worker
    worker = EmbeddingWorker(embedder, pinecone_client)
    
    if settings.rabbitmq_url:
        await worker.connect(settings.rabbitmq_url)
        
        # Start worker in background
        worker_task = asyncio.create_task(worker.start())
        logger.info("Worker task created and started")
    else:
        logger.error("RabbitMQ URL not provided!")
        raise ValueError("RABBITMQ_URL is required")
    
    logger.info("Vectorization Service started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global worker, worker_task
    
    logger.info("Shutting down Vectorization Service...")
    
    # Stop worker
    if worker:
        await worker.stop()
    
    if worker_task:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
    
    # Disconnect from MongoDB
    await mongodb_client.disconnect()
    
    # Flush Langfuse
    if langfuse_client.is_enabled():
        langfuse_client.flush()
    
    logger.info("Vectorization Service shut down successfully")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    mongo_healthy = await mongodb_client.health_check()
    
    # Check Pinecone
    pinecone_healthy = False
    if pinecone_client:
        try:
            stats = pinecone_client.get_index_stats()
            pinecone_healthy = bool(stats)
        except Exception:
            pinecone_healthy = False
    
    return {
        "status": "healthy" if (mongo_healthy and pinecone_healthy) else "degraded",
        "service": "vectorization-service",
        "mongodb": "connected" if mongo_healthy else "disconnected",
        "pinecone": "connected" if pinecone_healthy else "disconnected",
        "worker": "running" if worker and worker._running else "stopped"
    }


@app.get("/stats")
async def get_stats():
    """Get vectorization statistics."""
    stats = {}
    
    if pinecone_client:
        try:
            stats['pinecone'] = pinecone_client.get_index_stats()
        except Exception as e:
            stats['pinecone_error'] = str(e)
    
    # Get processing stats from MongoDB
    db = mongodb_client.get_database()
    
    total_content = await db.content.count_documents({})
    completed = await db.content.count_documents({"status": "completed"})
    processing = await db.content.count_documents({"status": "processing"})
    failed = await db.content.count_documents({"status": "failed"})
    
    stats['content'] = {
        "total": total_content,
        "completed": completed,
        "processing": processing,
        "failed": failed
    }
    
    return stats


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

