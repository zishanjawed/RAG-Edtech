"""
RAG Query Service - Question answering with streaming responses.
"""
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from uuid import uuid4
from datetime import datetime
import sys
import os

# Add services directory to path for classifier import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from pipeline.rag_pipeline import RAGPipeline
from retrieval.pinecone_retriever import PineconeRetriever
from llm.openai_client import OpenAIClient
from cache.redis_cache import ResponseCache
from models.schemas import QuestionRequest, QuestionResponse, SourceReference, GlobalChatRequest
from config import settings
from shared.database.mongodb_client import mongodb_client, get_mongodb
from shared.database.redis_client import redis_client
from shared.observability.langfuse_client import langfuse_client
from shared.middleware.error_handler import register_exception_handlers
from shared.logging.logger import get_logger

# Import question classifier
try:
    from services.analytics.nlp.question_classifier import classify_question
    logger_temp = get_logger("rag-query", "INFO")
    logger_temp.info("Question classifier imported successfully")
except ImportError as e:
    logger_temp = get_logger("rag-query", "INFO")
    logger_temp.warning(f"Could not import question classifier: {e}. Questions will not be classified.")
    def classify_question(question):
        return ("general", 0.5)

logger = get_logger(settings.service_name, settings.log_level)

# Create FastAPI app
app = FastAPI(
    title="RAG Edtech - RAG Query Service",
    description="Question answering service with RAG pipeline",
    version="1.0.0"
)

# Add CORS middleware (centralized configuration)
from shared.middleware.cors_config import configure_cors
configure_cors(app, settings.cors_origins)

# Register exception handlers
register_exception_handlers(app)

# Initialize components
rag_pipeline = None


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup."""
    global rag_pipeline
    
    logger.info("Starting RAG Query Service...")
    
    # Connect to MongoDB
    await mongodb_client.connect(
        settings.mongodb_url,
        settings.mongodb_database
    )
    
    # Connect to Redis
    await redis_client.connect(settings.redis_url)
    
    # Initialize components
    retriever = PineconeRetriever(
        api_key=settings.pinecone_api_key,
        environment=settings.pinecone_environment,
        index_name=settings.pinecone_index_name,
        top_k=settings.top_k_results
    )
    retriever.connect()
    
    llm_client = OpenAIClient(
        api_key=settings.openai_api_key,
        model=settings.llm_model
    )
    
    cache = ResponseCache(ttl_seconds=settings.cache_ttl_seconds)
    
    # Initialize RAG pipeline
    rag_pipeline = RAGPipeline(retriever, llm_client, cache)
    
    # Initialize Langfuse
    if settings.langfuse_public_key and settings.langfuse_secret_key:
        langfuse_client.initialize(
            settings.langfuse_public_key,
            settings.langfuse_secret_key,
            settings.langfuse_host
        )
    
    # Create indexes
    db = mongodb_client.get_database()
    await db.questions.create_index("content_id")
    await db.questions.create_index("student_id")
    await db.questions.create_index("timestamp")
    await db.questions.create_index("is_global")  # For global question queries
    await db.questions.create_index("searched_doc_ids")  # For tracking doc access
    
    logger.info("RAG Query Service started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down RAG Query Service...")
    await mongodb_client.disconnect()
    await redis_client.disconnect()
    
    # Properly shutdown Langfuse (flush all pending traces)
    if langfuse_client.is_enabled():
        langfuse_client.shutdown()
    
    logger.info("RAG Query Service shut down successfully")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    mongo_healthy = await mongodb_client.health_check()
    redis_healthy = await redis_client.health_check()
    
    return {
        "status": "healthy" if (mongo_healthy and redis_healthy) else "degraded",
        "service": "rag-query-service",
        "mongodb": "connected" if mongo_healthy else "disconnected",
        "redis": "connected" if redis_healthy else "disconnected"
    }


@app.post("/api/query/{content_id}")
async def ask_question_stream(
    content_id: str,
    request_data: QuestionRequest,
    request: Request,
    db=Depends(get_mongodb)
):
    """
    Ask a question and get streaming response.
    
    Args:
        content_id: Content ID to query
        request_data: Question request data
        request: Request object for headers
        db: MongoDB database instance
    
    Returns:
        Streaming response with answer
    """
    # Get or generate session ID
    session_id = request.headers.get("X-Session-ID", str(uuid4()))
    
    logger.info(f"Question asked for content {content_id} by user {request_data.user_id} (session: {session_id})")
    
    question_id = str(uuid4())
    start_time = datetime.utcnow()
    
    # Stream the response
    async def generate():
        try:
            response_text = ""
            
            async for chunk in rag_pipeline.process_query_stream(
                content_id=content_id,
                question=request_data.question,
                user_id=request_data.user_id,
                session_id=session_id,
                student_id=getattr(request_data, 'student_id', request_data.user_id),
                metadata={
                    "subject": getattr(request_data, 'subject', None),
                    "grade_level": getattr(request_data, 'grade_level', None)
                }
            ):
                response_text += chunk
                yield chunk
            
            # Classify question type
            question_type, classification_confidence = classify_question(request_data.question)
            
            # Store Q&A in MongoDB
            question_doc = {
                "question_id": question_id,
                "content_id": content_id,
                "session_id": session_id,
                "student_id": getattr(request_data, 'student_id', request_data.user_id),
                "question_text": request_data.question,
                "answer_text": response_text,
                "timestamp": start_time,
                "response_time_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000),
                "cached": False,
                "question_type": question_type,
                "classification_confidence": classification_confidence,
                "metadata": {
                    "subject": getattr(request_data, 'subject', None),
                    "grade_level": getattr(request_data, 'grade_level', None)
                }
            }
            
            await db.questions.insert_one(question_doc)
            
        except Exception as e:
            logger.error(f"Error in streaming response: {str(e)}")
            yield f"\n\nError: {str(e)}"
    
    return StreamingResponse(generate(), media_type="text/plain")


@app.post("/api/query/{content_id}/complete", response_model=QuestionResponse)
async def ask_question_complete(
    content_id: str,
    request_data: QuestionRequest,
    request: Request,
    db=Depends(get_mongodb)
):
    """
    Ask a question and get complete response (non-streaming).
    
    Args:
        content_id: Content ID to query
        request_data: Question request data
        request: Request object for headers
        db: MongoDB database instance
    
    Returns:
        Complete response with answer
    """
    # Get or generate session ID
    session_id = request.headers.get("X-Session-ID", str(uuid4()))
    
    logger.info(f"Question asked for content {content_id} by user {request_data.user_id} (session: {session_id})")
    
    question_id = str(uuid4())
    
    # Process query
    result = await rag_pipeline.process_query(
        content_id=content_id,
        question=request_data.question,
        user_id=request_data.user_id,
        session_id=session_id,
        student_id=getattr(request_data, 'student_id', request_data.user_id),
        metadata={
            "subject": getattr(request_data, 'subject', None),
            "grade_level": getattr(request_data, 'grade_level', None)
        }
    )
    
    # Classify question type
    question_type, classification_confidence = classify_question(request_data.question)
    
    # Store Q&A in MongoDB
    question_doc = {
        "question_id": question_id,
        "content_id": content_id,
        "session_id": session_id,
        "student_id": getattr(request_data, 'student_id', request_data.user_id),
        "question_text": request_data.question,
        "answer_text": result['response'],
        "timestamp": datetime.utcnow(),
        "response_time_ms": result['metadata']['response_time_ms'],
        "tokens_used": result['metadata'].get('tokens_used', {}),
        "cached": result['cached'],
        "question_type": question_type,
        "classification_confidence": classification_confidence,
        "metadata": {
            "subject": getattr(request_data, 'subject', None),
            "grade_level": getattr(request_data, 'grade_level', None)
        }
    }
    
    await db.questions.insert_one(question_doc)
    
    return QuestionResponse(
        question_id=question_id,
        content_id=content_id,
        question=request_data.question,
        answer=result['response'],
        sources=[SourceReference(**src) for src in result.get('sources', [])],
        metadata=result['metadata'],
        cached=result['cached']
    )


@app.post("/api/query/global/complete", response_model=QuestionResponse)
async def global_chat_complete(
    request_data: GlobalChatRequest,
    request: Request,
    db=Depends(get_mongodb)
):
    """
    Global chat across multiple documents with @-mention support.
    
    Args:
        request_data: Global chat request with optional selected_doc_ids
        request: Request object
        db: MongoDB database instance
    
    Returns:
        Complete response with sources from multiple documents
    """
    from access_control import get_user_accessible_docs, filter_accessible_docs
    
    session_id = request.headers.get("X-Session-ID", str(uuid4()))
    question_id = str(uuid4())
    
    logger.info(f"Global chat query by user {request_data.user_id}: {request_data.question[:100]}")
    
    # Get user to determine role
    user = await db.users.find_one({"user_id": request_data.user_id})
    role = user.get("role", "student") if user else "student"
    
    # Determine which documents to search
    if request_data.selected_doc_ids:
        # User selected specific docs via @mentions - filter to accessible only
        doc_ids = await filter_accessible_docs(
            user_id=request_data.user_id,
            doc_ids=request_data.selected_doc_ids,
            role=role
        )
        logger.info(f"User selected {len(request_data.selected_doc_ids)} docs, {len(doc_ids)} accessible")
    else:
        # Search all accessible documents
        doc_ids = await get_user_accessible_docs(request_data.user_id, role)
        logger.info(f"Searching across {len(doc_ids)} accessible documents")
    
    if not doc_ids:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail="No accessible documents found. Please upload a document first."
        )
    
    # Query Pinecone with content_id filter
    import time
    start_time = time.time()
    
    # Get embeddings for question
    retrieval_start = time.time()
    query_embedding = await rag_pipeline.llm_client.embedder.embed_query(request_data.question)
    
    # Query with filter for multiple documents
    results = await rag_pipeline.retriever.search_global(
        query_vector=query_embedding,
        content_ids=doc_ids,
        top_k=10  # Get more results for global search
    )
    
    retrieval_time = int((time.time() - retrieval_start) * 1000)
    
    # Diversify results (max 2 chunks per document, 8 total)
    diverse_results = diversify_search_results(results, max_per_doc=2, max_total=8)
    
    logger.info(f"Retrieved {len(diverse_results)} diverse chunks from {len(set(r.metadata.get('content_id') for r in diverse_results))} documents")
    
    # Build context from diverse results
    context = "\n\n---\n\n".join([
        f"[Source {i+1} - {r.metadata.get('document_title', 'Unknown')}]\n{r.metadata['text']}"
        for i, r in enumerate(diverse_results)
    ])
    
    # Generate answer
    llm_start = time.time()
    from prompts.educational_prompts import create_global_rag_prompt
    
    prompt = create_global_rag_prompt(context, request_data.question, len(doc_ids))
    
    answer = await rag_pipeline.llm_client.generate_completion(prompt)
    llm_time = int((time.time() - llm_start) * 1000)
    
    # Format sources
    sources = []
    for i, result in enumerate(diverse_results):
        sources.append(SourceReference(
            source_id=i + 1,
            document_title=result.metadata.get('document_title', 'Unknown'),
            uploader_name=result.metadata.get('uploader_name', 'Unknown'),
            uploader_id=result.metadata.get('uploader_id', ''),
            upload_date=result.metadata.get('upload_date', '').split('T')[0] if result.metadata.get('upload_date') else '',
            chunk_index=result.metadata.get('chunk_index', 0),
            similarity_score=result.score
        ))
    
    total_time = int((time.time() - start_time) * 1000)
    
    # Store question in MongoDB
    question_doc = {
        "question_id": question_id,
        "session_id": session_id,
        "student_id": request_data.user_id,
        "question_text": request_data.question,
        "answer_text": answer,
        "timestamp": datetime.utcnow(),
        "response_time_ms": total_time,
        "cached": False,
        "is_global": True,
        "searched_doc_ids": doc_ids,
        "documents_searched": len(doc_ids),
        "selected_doc_ids": request_data.selected_doc_ids or []
    }
    
    await db.questions.insert_one(question_doc)
    
    return QuestionResponse(
        question_id=question_id,
        content_id="global",  # Special marker for global queries
        question=request_data.question,
        answer=answer,
        sources=sources,
        metadata={
            "chunks_used": len(diverse_results),
            "documents_searched": len(doc_ids),
            "response_time_ms": total_time,
            "llm_time_ms": llm_time,
            "retrieval_time_ms": retrieval_time,
            "tokens_used": {
                "prompt_tokens": len(prompt.split()) * 1.3,  # Rough estimate
                "completion_tokens": len(answer.split()) * 1.3,
                "total_tokens": (len(prompt) + len(answer)) // 4
            },
            "model": "gpt-4-0613"
        },
        cached=False
    )


def diversify_search_results(results, max_per_doc=2, max_total=8):
    """
    Diversify search results to include chunks from multiple documents.
    
    Args:
        results: List of search results with metadata
        max_per_doc: Maximum chunks per document (default: 2)
        max_total: Maximum total chunks (default: 8)
    
    Returns:
        Diversified list of results
    """
    by_doc = {}
    for match in results:
        doc_id = match.metadata.get('content_id')
        if doc_id not in by_doc:
            by_doc[doc_id] = []
        by_doc[doc_id].append(match)
    
    # Round-robin selection for diversity
    diverse = []
    round_num = 0
    
    while len(diverse) < max_total and any(by_doc.values()):
        for doc_id, matches in list(by_doc.items()):
            if not matches:
                continue
            
            # Count how many chunks from this doc we already have
            doc_count = len([m for m in diverse if m.metadata.get('content_id') == doc_id])
            
            if doc_count < max_per_doc:
                diverse.append(matches.pop(0))
                if len(diverse) >= max_total:
                    break
        
        round_num += 1
        if round_num > 10:  # Safety break
            break
    
    return diverse[:max_total]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

