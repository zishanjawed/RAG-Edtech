"""
Document Processing Service - Handles document upload, parsing, and chunking.
"""
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import os
from uuid import uuid4
from datetime import datetime

from parsers.docling_parser import DoclingParser, save_uploaded_file
from chunking.chunker_factory import get_chunker
from publisher.rabbitmq_publisher import rabbitmq_publisher
from models.schemas import DocumentUploadResponse, ContentMetadata
from deletion_service import deletion_service
from config import settings
from shared.database.mongodb_client import mongodb_client, get_mongodb
from shared.database.redis_client import redis_client
from shared.observability.langfuse_client import langfuse_client
from shared.middleware.error_handler import register_exception_handlers
from shared.exceptions.custom_exceptions import (
    DocumentProcessingError,
    ValidationError,
    FileValidationError
)
from shared.logging.logger import get_logger
from shared.utils.content_hash import content_hasher

logger = get_logger(settings.service_name, settings.log_level)

# Create FastAPI app
app = FastAPI(
    title="RAG Edtech - Document Processor",
    description="Document upload, parsing, and chunking service",
    version="1.0.0"
)

# Add CORS middleware (centralized configuration)
from shared.middleware.cors_config import configure_cors
configure_cors(app, settings.cors_origins)

# Register exception handlers
register_exception_handlers(app)

# Initialize parser and chunker
docling_parser = DoclingParser()

# Get chunker from factory (configured via CHUNKING_STRATEGY env var)
try:
    chunker = get_chunker(
        strategy=getattr(settings, 'chunking_strategy', None),
        max_tokens=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        merge_peers=getattr(settings, 'chunking_merge_peers', True)
    )
    chunking_strategy = getattr(settings, 'chunking_strategy', os.getenv('CHUNKING_STRATEGY', 'docling'))
    logger.info(f"[OK] Chunker initialized with strategy: {chunking_strategy}")
except Exception as e:
    logger.error(f"Failed to initialize chunker: {str(e)}")
    raise


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup."""
    logger.info("Starting Document Processing Service...")
    
    # Connect to MongoDB
    await mongodb_client.connect(
        settings.mongodb_url,
        settings.mongodb_database
    )
    
    # Connect to RabbitMQ
    await rabbitmq_publisher.connect(settings.rabbitmq_url)
    
    # Initialize Langfuse
    if settings.langfuse_public_key and settings.langfuse_secret_key:
        langfuse_client.initialize(
            settings.langfuse_public_key,
            settings.langfuse_secret_key,
            settings.langfuse_host
        )
    
    # Create indexes
    db = mongodb_client.get_database()
    await db.content.create_index("content_id")
    await db.content.create_index("user_id")
    await db.content.create_index("upload_date")
    await db.content.create_index("content_hash")  # For deduplication
    await db.content.create_index("original_uploader_id")  # For traceability
    await db.content.create_index("parent_content_id")  # For version tracking
    await db.content.create_index("tags")  # For filtering by tags
    await db.suggested_questions.create_index("content_id")  # For question lookups
    await db.suggested_questions.create_index("created_at")  # For sorting
    
    logger.info("Document Processing Service started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Document Processing Service...")
    await mongodb_client.disconnect()
    await rabbitmq_publisher.disconnect()
    
    # Properly shutdown Langfuse (flush all pending traces)
    if langfuse_client.is_enabled():
        langfuse_client.shutdown()
    
    logger.info("Document Processing Service shut down successfully")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    mongo_healthy = await mongodb_client.health_check()
    
    return {
        "status": "healthy" if mongo_healthy else "unhealthy",
        "service": "document-processor",
        "mongodb": "connected" if mongo_healthy else "disconnected",
        "rabbitmq": "connected" if rabbitmq_publisher.connection else "disconnected"
    }


@app.websocket("/ws/document/{content_id}/status")
async def websocket_status_endpoint(websocket: WebSocket, content_id: str):
    """
    WebSocket endpoint for real-time document processing status updates.
    
    Usage:
        const ws = new WebSocket('ws://localhost:8002/ws/document/{content_id}/status')
        ws.onmessage = (event) => {
            const status = JSON.parse(event.data)
            // status: { status, progress, processed_chunks, total_chunks, message }
        }
    """
    from websocket_handler import websocket_endpoint
    await websocket_endpoint(websocket, content_id)


@app.delete("/api/content/{content_id}")
async def delete_content(
    content_id: str,
    user_id: str,
    db=Depends(get_mongodb)
):
    """
    Delete a document and all associated data.
    
    This performs a complete deletion:
    - MongoDB content record
    - Pinecone vectors (entire namespace)
    - Physical file from uploads directory
    - Redis cache entries
    - Related questions
    
    Args:
        content_id: Content ID to delete
        user_id: User requesting deletion (from auth middleware)
        db: MongoDB database instance
    
    Returns:
        Deletion confirmation
    
    Raises:
        HTTPException: If document not found or user lacks permission
    """
    logger.info(f"Delete request for content {content_id} by user {user_id}")
    
    # Get document from MongoDB
    content_doc = await db.content.find_one({"content_id": content_id})
    
    if not content_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {content_id} not found"
        )
    
    # Get user to check permissions
    user = await db.users.find_one({"user_id": user_id})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Check permissions: User must be the owner or a teacher
    is_owner = content_doc.get('user_id') == user_id or content_doc.get('original_uploader_id') == user_id
    is_teacher = user.get('role') == 'teacher'
    is_uploader = any(
        entry.get('user_id') == user_id 
        for entry in content_doc.get('upload_history', [])
    )
    
    if not (is_owner or is_teacher or is_uploader):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this document"
        )
    
    logger.info(f"Permission granted for deletion (owner: {is_owner}, teacher: {is_teacher}, uploader: {is_uploader})")
    
    # Perform complete deletion
    # Note: Pinecone client not available in document-processor, deletion handled asynchronously
    deletion_stats = await deletion_service.delete_document_complete(
        content_id=content_id,
        pinecone_client=None  # Will be handled by separate service if needed
    )
    
    return {
        "content_id": content_id,
        "filename": content_doc.get('filename'),
        "message": "Document deleted successfully",
        "deletion_stats": deletion_stats
    }


@app.post("/api/content/upload", response_model=DocumentUploadResponse)
async def upload_content(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    title: str = Form(None),
    description: str = Form(None),
    subject: str = Form(None),
    tags: str = Form(None),  # Comma-separated tags
    instructor_id: str = Form(None),
    grade_level: str = Form(None),  # Optional, kept for backward compatibility
    db=Depends(get_mongodb)
):
    """
    Upload and process educational content.
    
    Args:
        file: Uploaded file (PDF, MD, TXT, DOCX)
        user_id: ID of the user uploading the content
        title: Optional content title
        description: Optional content description
        subject: Optional subject area - accepts any string (e.g., Chemistry, Physics, Biology)
        tags: Optional comma-separated tags for filtering
        instructor_id: Optional instructor/teacher ID
        grade_level: Optional grade level (backward compatibility)
        db: MongoDB database instance
    
    Returns:
        Upload response with content ID and status
    
    Raises:
        FileValidationError: If file validation fails
        DocumentProcessingError: If processing fails
    """
    logger.info(f"Upload request from user {user_id}: {file.filename} " +
                (f"({subject})" if subject else ""))
    
    # Validate file type
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in ['pdf', 'md', 'txt']:
        raise FileValidationError(
            "Unsupported file type. Allowed types: PDF, MD, TXT",
            details={"filename": file.filename, "extension": file_extension}
        )
    
    # Validate file size
    file_content = await file.read()
    file_size_mb = len(file_content) / (1024 * 1024)
    
    if file_size_mb > settings.max_file_size_mb:
        raise FileValidationError(
            f"File too large. Maximum size: {settings.max_file_size_mb}MB",
            details={"file_size_mb": file_size_mb, "max_size_mb": settings.max_file_size_mb}
        )
    
    # Generate content ID
    content_id = str(uuid4())
    
    # Prepare langfuse tags (different from document tags)
    langfuse_tags = ["document_upload"]
    if subject:
        langfuse_tags.append(subject.lower())
    if grade_level:
        langfuse_tags.append(f"grade_{grade_level}")
    
    # Start Langfuse trace with enhanced metadata
    trace = None
    if langfuse_client.is_enabled():
        try:
            trace = langfuse_client.client.trace(
                name="document_upload",
                user_id=user_id,
                metadata={
                    "content_id": content_id,
                    "filename": file.filename,
                    "file_size_mb": round(file_size_mb, 2),
                    "file_type": file_extension,
                    "title": title,
                    "subject": subject,
                    "grade_level": grade_level,
                    "instructor_id": instructor_id,
                    "description": description
                },
                tags=langfuse_tags
            )
        except Exception as e:
            logger.warning(f"Failed to create Langfuse trace: {str(e)}")
    
    try:
        # Save file temporarily
        file_path = save_uploaded_file(file_content, file.filename)
        
        logger.info(f"Processing document: {file_path}")
        
        # Parse document with observations
        with langfuse_client.create_observation(
            name="parse_document",
            trace_id=trace.id if trace else None,
            input_data={"filename": file.filename, "file_type": file_extension, "file_size_mb": round(file_size_mb, 2)}
        ) as parse_obs:
            parsed_doc = docling_parser.parse_document(file_path, file_extension)
            
            parse_obs.set_output({
                "title": parsed_doc['title'],
                "page_count": parsed_doc['metadata'].get('page_count', 1),
                "content_length": len(parsed_doc['content']),
                "tables_found": len(parsed_doc['metadata'].get('tables', [])),
                "figures_found": len(parsed_doc['metadata'].get('figures', []))
            })
        
        # Chunk document with observations
        with langfuse_client.create_observation(
            name="chunk_document",
            trace_id=trace.id if trace else None,
            input_data={"content_length": len(parsed_doc['content'])},
            metadata={"chunking_strategy": os.getenv('CHUNKING_STRATEGY', 'token_based')}
        ) as chunk_obs:
            chunks = chunker.chunk_document(
                content=parsed_doc['content'],
                metadata=parsed_doc['metadata'],
                structure=parsed_doc['structure']
            )
            
            # Calculate chunk statistics
            chunk_sizes = [chunk.get('token_count', 0) for chunk in chunks]
            avg_chunk_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0
            
            chunk_obs.set_output({
                "total_chunks": len(chunks),
                "avg_chunk_size": round(avg_chunk_size, 1),
                "min_chunk_size": min(chunk_sizes) if chunk_sizes else 0,
                "max_chunk_size": max(chunk_sizes) if chunk_sizes else 0,
                "chunking_strategy": chunks[0]['metadata'].get('chunking_strategy', 'unknown') if chunks else 'unknown'
            })
        
        logger.info(f"Created {len(chunks)} chunks from document {file.filename}")
        
        # Generate content hash for deduplication
        content_hash = content_hasher.generate_content_hash(parsed_doc['content'])
        logger.info(f"Generated content hash: {content_hash[:16]}...")
        
        # Check for duplicate content
        existing_doc = await db.content.find_one({"content_hash": content_hash})
        
        if existing_doc:
            # Duplicate found - update upload history instead of reprocessing
            logger.info(f"Duplicate content detected! Existing content_id: {existing_doc['content_id']}")
            
            # Get uploader name
            user = await db.users.find_one({"user_id": user_id})
            uploader_name = user.get('full_name', 'Unknown') if user else 'Unknown'
            
            # Add to upload history
            upload_history_entry = {
                "user_id": user_id,
                "user_name": uploader_name,
                "upload_date": datetime.utcnow(),
                "filename": file.filename,
                "content_hash": content_hash
            }
            
            await db.content.update_one(
                {"content_id": existing_doc['content_id']},
                {
                    "$push": {"upload_history": upload_history_entry},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            logger.info(f"Added upload history entry for user {uploader_name}")
            
            # Return response indicating duplicate
            return DocumentUploadResponse(
                content_id=existing_doc['content_id'],
                filename=file.filename,
                file_type=file_extension,
                status=existing_doc.get('status', 'completed'),
                total_chunks=existing_doc.get('total_chunks', 0),
                message="Document already exists in knowledge base. Linked to your account.",
                is_duplicate=True,
                duplicate_of=existing_doc['content_id']
            )
        
        # New document - process normally
        logger.info("New document - processing...")
        
        # Get uploader name for tracking
        user = await db.users.find_one({"user_id": user_id})
        uploader_name = user.get('full_name', 'Unknown') if user else 'Unknown'
        
        # Create initial upload history entry
        upload_history_entry = {
            "user_id": user_id,
            "user_name": uploader_name,
            "upload_date": datetime.utcnow(),
            "filename": file.filename,
            "content_hash": content_hash
        }
        
        # Parse tags from comma-separated string
        tags_list = []
        if tags:
            tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Store metadata in MongoDB with deduplication fields
        content_metadata = ContentMetadata(
            content_id=content_id,
            filename=file.filename,
            file_type=file_extension,
            user_id=user_id,
            content_hash=content_hash,
            is_duplicate=False,
            original_uploader_id=user_id,
            original_upload_date=datetime.utcnow(),
            upload_history=[upload_history_entry],
            version_number=1,
            parent_content_id=None,
            status="processing",
            total_chunks=len(chunks),
            tags=tags_list,  # Store parsed tags
            metadata={
                "title": parsed_doc['title'],
                "page_count": parsed_doc['metadata'].get('page_count', 1),
                "file_size": file_size_mb,
                "tables": len(parsed_doc['metadata'].get('tables', [])),
                "figures": len(parsed_doc['metadata'].get('figures', [])),
                "uploader_name": uploader_name,
                "subject": subject or "General",
                "grade_level": grade_level or ""
            }
        )
        
        await db.content.insert_one(content_metadata.model_dump())
        
        # Enhance chunks with source metadata before publishing
        for chunk in chunks:
            chunk['metadata']['document_title'] = parsed_doc['title']
            chunk['metadata']['uploader_name'] = uploader_name
            chunk['metadata']['uploader_id'] = user_id
            chunk['metadata']['upload_date'] = datetime.utcnow().isoformat()
            chunk['metadata']['subject'] = subject or "General"
            chunk['metadata']['grade_level'] = grade_level or ""
            chunk['metadata']['tags'] = tags_list
        
        # Publish chunks to RabbitMQ with observations
        with langfuse_client.create_observation(
            name="publish_chunks",
            trace_id=trace.id if trace else None,
            input_data={"chunk_count": len(chunks), "content_id": content_id}
        ) as publish_obs:
            await rabbitmq_publisher.publish_chunks(chunks, content_id)
            publish_obs.set_output({"published": True, "chunk_count": len(chunks)})
        
        # Publish WebSocket status update
        try:
            from websocket_handler import manager
            await manager.publish_status(content_id, {
                "status": "processing",
                "progress": 10,
                "processed_chunks": 0,
                "total_chunks": len(chunks),
                "message": f"Processing {len(chunks)} chunks..."
            })
        except Exception as e:
            logger.warning(f"Failed to publish WebSocket status: {e}")
        
        # Clean up temp file
        try:
            os.remove(file_path)
        except Exception:
            pass
        
        # Update trace with final output
        if trace:
            try:
                trace.update(
                    output={
                        "content_id": content_id,
                        "status": "processing",
                        "total_chunks": len(chunks)
                    },
                    metadata={
                        "content_id": content_id,
                        "filename": file.filename,
                        "file_type": file_extension,
                        "chunks_created": len(chunks),
                        "avg_chunk_size": round(avg_chunk_size, 1),
                        "subject": subject,
                        "grade_level": grade_level
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to update trace: {str(e)}")
        
        logger.info(f"Successfully processed document {file.filename} (content_id: {content_id})")
        
        # Generate suggested questions in background (don't block upload response)
        import asyncio
        asyncio.create_task(
            generate_and_store_questions(
                content_id=content_id,
                title=parsed_doc['title'],
                subject=subject or "General",
                content_preview=parsed_doc['content'],
                tags=tags_list
            )
        )
        
        return DocumentUploadResponse(
            content_id=content_id,
            filename=file.filename,
            file_type=file_extension,
            status="processing",
            total_chunks=len(chunks),
            message=f"Document uploaded successfully. Processing {len(chunks)} chunks."
        )
        
    except Exception as e:
        # Update status to failed
        await db.content.update_one(
            {"content_id": content_id},
            {"$set": {"status": "failed"}}
        )
        
        # Log error to trace
        if trace:
            try:
                trace.update(
                    level="ERROR",
                    status_message=str(e),
                    metadata={
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "filename": file.filename
                    }
                )
            except Exception as update_error:
                logger.warning(f"Failed to log error to trace: {str(update_error)}")
        
        logger.error(f"Failed to process document {file.filename}: {str(e)}")
        
        raise DocumentProcessingError(
            f"Failed to process document: {str(e)}",
            details={"filename": file.filename, "content_id": content_id}
        )


@app.get("/api/content/{content_id}/status")
async def get_content_status(content_id: str, db=Depends(get_mongodb)):
    """
    Get processing status of a content.
    
    Args:
        content_id: Content ID
        db: MongoDB database instance
    
    Returns:
        Content status information
    """
    content = await db.content.find_one({"content_id": content_id})
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with ID {content_id} not found"
        )
    
    return {
        "content_id": content_id,
        "filename": content['filename'],
        "status": content['status'],
        "total_chunks": content['total_chunks'],
        "processed_chunks": content.get('processed_chunks', 0),
        "upload_date": content['upload_date']
    }


@app.get("/api/content/user/{user_id}")
async def get_user_documents(
    user_id: str,
    filter: str = "all",  # all, owned, shared
    search: str = None,
    subjects: str = None,  # comma-separated
    tags: str = None,  # comma-separated
    page: int = 1,
    limit: int = 50,
    db=Depends(get_mongodb)
):
    """
    Get documents for a user with filtering and search.
    
    Query Parameters:
        - filter: all/owned/shared (default: all)
        - search: search in title/subject/tags
        - subjects: comma-separated subjects to filter
        - tags: comma-separated tags to filter
        - page: page number (default: 1)
        - limit: results per page (default: 50)
    
    Returns:
        Paginated list of documents with metadata
    """
    logger.info(f"Getting documents for user {user_id}, filter={filter}, search={search}")
    
    # Build base query
    base_query = {}
    
    # Apply ownership filter
    if filter == "owned":
        base_query["user_id"] = user_id
    elif filter == "shared":
        # Documents in upload_history but not owned
        base_query = {
            "upload_history.user_id": user_id,
            "user_id": {"$ne": user_id}
        }
    else:  # all
        base_query = {
            "$or": [
                {"user_id": user_id},
                {"upload_history.user_id": user_id}
            ]
        }
    
    # Build search/filter conditions
    conditions = []
    
    # Apply search
    if search:
        search_conditions = [
            {"metadata.title": {"$regex": search, "$options": "i"}},
            {"metadata.subject": {"$regex": search, "$options": "i"}},
            {"tags": {"$regex": search, "$options": "i"}},
            {"filename": {"$regex": search, "$options": "i"}}
        ]
        conditions.append({"$or": search_conditions})
    
    # Apply subject filter
    if subjects:
        subject_list = [s.strip() for s in subjects.split(",") if s.strip()]
        if subject_list:
            conditions.append({"metadata.subject": {"$in": subject_list}})
    
    # Apply tags filter
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            conditions.append({"tags": {"$in": tag_list}})
    
    # Combine all conditions
    if conditions:
        if "$or" in base_query or "$and" in base_query:
            # If base_query already has complex logic, wrap it
            final_query = {"$and": [base_query] + conditions}
        else:
            base_query["$and"] = conditions
            final_query = base_query
    else:
        final_query = base_query
    
    # Get total count
    total = await db.content.count_documents(final_query)
    
    # Get paginated results
    skip = (page - 1) * limit
    cursor = db.content.find(final_query).sort("upload_date", -1).skip(skip).limit(limit)
    documents = await cursor.to_list(length=limit)
    
    # Enhance documents with additional fields and convert to JSON-serializable format
    result_docs = []
    for doc in documents:
        # Remove MongoDB ObjectId
        if "_id" in doc:
            del doc["_id"]
        
        # Convert datetime to ISO string
        if "upload_date" in doc and hasattr(doc["upload_date"], "isoformat"):
            doc["upload_date"] = doc["upload_date"].isoformat()
        if "updated_at" in doc and hasattr(doc["updated_at"], "isoformat"):
            doc["updated_at"] = doc["updated_at"].isoformat()
        if "original_upload_date" in doc and hasattr(doc["original_upload_date"], "isoformat"):
            doc["original_upload_date"] = doc["original_upload_date"].isoformat()
        
        # Convert upload_history dates
        if "upload_history" in doc:
            for entry in doc["upload_history"]:
                if "upload_date" in entry and hasattr(entry["upload_date"], "isoformat"):
                    entry["upload_date"] = entry["upload_date"].isoformat()
        
        # Calculate is_owned and is_shared
        doc["is_owned"] = doc.get("user_id") == user_id
        doc["is_shared"] = not doc["is_owned"] and any(
            entry.get("user_id") == user_id
            for entry in doc.get("upload_history", [])
        )
        
        # Get last activity from questions collection
        last_question = await db.questions.find_one(
            {"content_id": doc["content_id"]},
            sort=[("created_at", -1)]
        )
        if last_question:
            last_activity = last_question.get("created_at")
            if hasattr(last_activity, "isoformat"):
                doc["last_activity"] = last_activity.isoformat()
            else:
                doc["last_activity"] = str(last_activity)
        else:
            doc["last_activity"] = doc.get("upload_date")
        
        # Get uploader name
        doc["uploader_name"] = doc.get("metadata", {}).get("uploader_name", "Unknown")
        
        # Add chunks_count for frontend display
        doc["chunks_count"] = doc.get("total_chunks", 0)
        
        result_docs.append(doc)
    
    logger.info(f"Returning {len(result_docs)} of {total} documents")
    
    return {
        "documents": result_docs,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit if limit > 0 else 1
    }


async def generate_and_store_questions(
    content_id: str,
    title: str,
    subject: str,
    content_preview: str,
    tags: list
):
    """
    Generate suggested questions and store them in MongoDB.
    Runs in background after document upload.
    """
    try:
        from question_generator import generate_questions_for_document
        
        logger.info(f"Generating questions for document {content_id}")
        
        questions = await generate_questions_for_document(
            content_id=content_id,
            title=title,
            subject=subject,
            content_preview=content_preview,
            tags=tags
        )
        
        # Store in MongoDB
        db = mongodb_client.get_database()
        if questions:
            await db.suggested_questions.insert_many(questions)
            logger.info(f"Stored {len(questions)} suggested questions for {content_id}")
        
    except Exception as e:
        logger.error(f"Failed to generate/store questions for {content_id}: {e}")


@app.get("/api/prompts/document/{content_id}")
async def get_document_prompts(
    content_id: str,
    db=Depends(get_mongodb)
):
    """
    Get suggested questions for a specific document.
    
    Args:
        content_id: Document ID
    
    Returns:
        List of suggested prompts/questions
    """
    # Try to get generated questions from database
    questions = await db.suggested_questions.find(
        {"content_id": content_id}
    ).to_list(length=5)
    
    if questions:
        # Format for frontend
        prompts = [
            {
                "id": q.get("id", q.get("_id")),
                "text": q.get("question"),
                "category": q.get("category"),
                "icon": get_category_icon(q.get("category"))
            }
            for q in questions
        ]
        return {"prompts": prompts}
    
    # If no questions generated yet, return fallback
    doc = await db.content.find_one({"content_id": content_id})
    
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {content_id} not found"
        )
    
    subject = doc.get("metadata", {}).get("subject", "General")
    tags = doc.get("tags", [])
    
    from question_generator import get_fallback_questions
    fallback = get_fallback_questions(content_id, subject, tags)
    
    prompts = [
        {
            "id": q["id"],
            "text": q["question"],
            "category": q["category"],
            "icon": get_category_icon(q["category"])
        }
        for q in fallback
    ]
    
    return {"prompts": prompts}


@app.get("/api/prompts/global")
async def get_global_prompts(
    user_id: str,
    db=Depends(get_mongodb)
):
    """
    Get suggested questions for global chat across user's documents.
    
    Args:
        user_id: User ID
    
    Returns:
        List of cross-document prompts
    """
    from shared.database.redis_client import redis_client
    import json
    
    # Check cache first
    cache_key = f"global_prompts:{user_id}"
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception:
        pass
    
    # Get user's documents
    cursor = db.content.find(
        {
            "$or": [
                {"user_id": user_id},
                {"upload_history.user_id": user_id}
            ],
            "status": "completed"
        }
    )
    documents = await cursor.to_list(length=None)
    
    if not documents:
        # Return generic prompts
        return {
            "prompts": [
                {"id": "g1", "text": "Tell me about the documents I've uploaded", "category": "explanation"},
                {"id": "g2", "text": "Help me create a study plan", "category": "evaluation"},
                {"id": "g3", "text": "What topics should I review?", "category": "evaluation"}
            ]
        }
    
    # Generate global questions
    from question_generator import generate_global_questions
    
    questions = await generate_global_questions(user_id, documents)
    
    prompts = [
        {
            "id": q["id"],
            "text": q["question"],
            "category": q["category"],
            "icon": get_category_icon(q["category"])
        }
        for q in questions
    ]
    
    result = {"prompts": prompts}
    
    # Cache for 24 hours
    try:
        await redis_client.setex(cache_key, 86400, json.dumps(result))
    except Exception:
        pass
    
    return result


def get_category_icon(category: str) -> str:
    """Map category to icon name."""
    icons = {
        "definition": "book-open",
        "explanation": "lightbulb",
        "comparison": "scale",
        "procedure": "list-ordered",
        "application": "zap",
        "evaluation": "target"
    }
    return icons.get(category, "lightbulb")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

