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
from prompts.educational_prompts import create_global_rag_prompt
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
    
    cache = ResponseCache(
        ttl_seconds=settings.cache_ttl_seconds,
        frequency_threshold=settings.cache_frequency_threshold
    )
    
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
    from access_control import get_user_accessible_docs, filter_accessible_docs, get_completed_docs_for_search
    
    session_id = request.headers.get("X-Session-ID", str(uuid4()))
    question_id = str(uuid4())
    
    logger.info(f"Global chat query by user {request_data.user_id}: {request_data.question[:100]}")
    logger.info(f"[global_request] selected_doc_ids={getattr(request_data, 'selected_doc_ids', None)}")
    
    # Get user to determine role
    user = await db.users.find_one({"user_id": request_data.user_id})
    role = user.get("role", "student") if user else "student"
    
    # Read raw body to tolerate both snake_case and camelCase client payloads
    try:
        raw_body = await request.json()
        selected_from_raw = raw_body.get("selected_doc_ids") or raw_body.get("selectedDocIds")
    except Exception:
        selected_from_raw = None
    selected_ids = selected_from_raw or getattr(request_data, "selected_doc_ids", None) or []
    
    # Determine which documents to search
    if selected_ids:
        # User selected specific docs via @mentions - filter to accessible only
        accessible_doc_ids = await filter_accessible_docs(
            user_id=request_data.user_id,
            doc_ids=selected_ids,
            role=role
        )
        logger.info(f"[GLOBAL_CHAT] User selected {len(selected_ids)} docs, {len(accessible_doc_ids)} accessible")
        # Filter to only completed documents for search
        doc_ids = await get_completed_docs_for_search(accessible_doc_ids)
        logger.info(f"[GLOBAL_CHAT] After filtering: {len(doc_ids)} completed docs")
    else:
        # Search all accessible documents
        accessible_doc_ids = await get_user_accessible_docs(request_data.user_id, role)
        logger.info(f"[GLOBAL_CHAT] Found {len(accessible_doc_ids)} accessible documents for user {request_data.user_id} (role: {role})")
        logger.info(f"[GLOBAL_CHAT] Accessible doc IDs: {accessible_doc_ids[:5]}...")  # Log first 5 IDs
        # Filter to only completed documents for search
        doc_ids = await get_completed_docs_for_search(accessible_doc_ids)
        logger.info(f"[GLOBAL_CHAT] Completed docs for search: {len(doc_ids)} (excluding {len(accessible_doc_ids) - len(doc_ids)} processing)")
        logger.info(f"[GLOBAL_CHAT] Completed doc IDs: {doc_ids[:5]}...")  # Log first 5 IDs
    
    # Check if user has any accessible documents (including processing)
    if not accessible_doc_ids:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail="No accessible documents found. Please upload a document first."
        )
    
    # If no completed documents but user has accessible docs, return helpful message
    if not doc_ids:
        processing_count = len(accessible_doc_ids) - len(doc_ids)
        no_completed_message = f"""I found {len(accessible_doc_ids)} document(s) in your account, but {'they are' if processing_count > 1 else 'it is'} still being processed.

**What's happening?**
Your document(s) are being converted into searchable vectors. This usually takes 1-2 minutes after upload.

**What to do:**
1. Wait a moment and try again (processing continues in the background)
2. Check your Documents page to see the processing status
3. Once documents show "Ready" status, global chat will work automatically

The global chat will be available as soon as your documents finish processing!"""
        return QuestionResponse(
            question_id=question_id,
            content_id="global",
            question=request_data.question,
            answer=no_completed_message,
            sources=[],
            metadata={
                "chunks_used": 0,
                "documents_searched": 0,
                "documents_processing": processing_count,
                "response_time_ms": 0,
            },
            cached=False
        )
    
    # If user specified docs, route directly to per-document pipeline for the explicitly selected doc
    if selected_ids and len(selected_ids) >= 1:
        # Prefer the explicitly selected first ID to match document chat behavior.
        # Do NOT override it even if not present in filtered list to avoid encoding mismatch issues.
        single_cid = selected_ids[0]
        logger.info(f"[global_selected_doc] Using selected content_id={single_cid}")
        result = await rag_pipeline.process_query(
            content_id=single_cid,
            question=request_data.question,
            user_id=request_data.user_id,
            session_id=session_id,
            student_id=request_data.user_id,
            metadata={}
        )
        return QuestionResponse(
            question_id=question_id,
            content_id="global",
            question=request_data.question,
            answer=result['response'],
            sources=[SourceReference(**src) for src in result.get('sources', [])],
            metadata={
                **result['metadata'],
                "documents_searched": 1
            },
            cached=result['cached']
        )

    # Delegate to isolated GlobalQueryService
    import time
    start_time = time.time()
    from pipeline.global_query_service import GlobalQueryService
    gqs = GlobalQueryService(rag_pipeline, create_global_rag_prompt)
    answer, sources, metadata, diag = await gqs.run(
        question_id=question_id,
        user_id=request_data.user_id,
        question=request_data.question,
        doc_ids=doc_ids,
        selected_doc_ids=request_data.selected_doc_ids or [],
    )
    total_time = int((time.time() - start_time) * 1000)
    if not answer and len(sources) == 0:
        no_vectors_message = f"""I couldn't find any searchable content in your {len(doc_ids)} document(s).

**This usually means:**
1. Your documents are still being processed (takes 1-2 minutes after upload)
2. The documents may not have completed vectorization successfully

**What to do:**
1. **Check document status**: Go to your Documents page and verify all documents show "Ready" status
2. **Wait and retry**: If documents show "Processing", wait 1-2 minutes and try again
3. **Re-upload if needed**: If documents have been "Processing" for more than 5 minutes, try re-uploading them

**For existing documents added via scripts**: Run the vectorization script to create searchable vectors:
```bash
python scripts/vectorize_seeded_docs.py
```

The global chat will work automatically once your documents are fully processed!"""
        return QuestionResponse(
            question_id=question_id,
            content_id="global",
            question=request_data.question,
            answer=no_vectors_message,
            sources=[],
            metadata={
                "chunks_used": 0,
                "documents_searched": len(doc_ids),
                "response_time_ms": total_time,
                "llm_time_ms": metadata.get("llm_time_ms", 0),
                "retrieval_time_ms": metadata.get("retrieval_time_ms", 0),
                "tokens_used": metadata.get("tokens_used", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}),
                "model": metadata.get("model", "gpt-4"),
                "diagnostics": diag.to_dict()
            },
            cached=False
        )
    # Persist and return successful response
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
        content_id="global",
        question=request_data.question,
        answer=answer,
        sources=[SourceReference(**src) for src in sources],
        metadata={
            **metadata,
            "response_time_ms": total_time,
            "diagnostics": diag.to_dict()
        },
        cached=False
    )


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


@app.get("/api/query/{content_id}/popular")
async def get_popular_questions(
    content_id: str,
    limit: int = 10,
    offset: int = 0
):
    """
    Get popular questions for a document based on frequency.
    
    Args:
        content_id: Content ID to get popular questions for
        limit: Maximum number of questions to return (default: 10)
    
    Returns:
        List of popular questions with their frequencies
    """
    try:
        from shared.database.redis_client import redis_client
        import hashlib
        
        # Get all frequency keys for this content
        pattern = f"rag_frequency:{content_id}:*"
        
        # Note: In production, you'd use SCAN for large key sets
        # For now, we'll retrieve questions from MongoDB and check their frequencies
        questions_data = []
        
        # Get unique questions from MongoDB for this content
        db = mongodb_client.get_database()
        unique_questions = await db.questions.aggregate([
            {"$match": {"content_id": content_id}},
            {"$group": {
                "_id": "$question_text",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$skip": offset},
            {"$limit": limit * 2}  # Get more to account for filtering
        ]).to_list(limit * 2)
        
        # For each question, get its frequency from Redis and check if cached
        for q in unique_questions:
            question_text = q['_id']
            
            # Get frequency from Redis (SHA-256 for security)
            question_hash = hashlib.sha256(question_text.lower().encode()).hexdigest()
            frequency_key = f"rag_frequency:{content_id}:{question_hash}"
            cache_key = f"rag_cache:{content_id}:{question_hash}"
            
            try:
                frequency = await redis_client.get(frequency_key)
                frequency = int(frequency) if frequency else 0
                
                # Check if cached
                is_cached = await redis_client.exists(cache_key)
                
                if frequency > 0:  # Only include questions with frequency tracking
                    questions_data.append({
                        "question": question_text,
                        "frequency": frequency,
                        "is_cached": is_cached
                    })
            except Exception as e:
                logger.error(f"Failed to get frequency for question: {str(e)}")
                continue
        
        # Sort by frequency and limit
        questions_data.sort(key=lambda x: x['frequency'], reverse=True)
        questions_data = questions_data[:limit]
        
        return {"popular_questions": questions_data, "total": len(questions_data)}
        
    except Exception as e:
        logger.error(f"Failed to get popular questions: {str(e)}")
        return {"popular_questions": [], "total": 0}


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

