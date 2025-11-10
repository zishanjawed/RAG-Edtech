"""
API Gateway - Main entry point for all client requests.
Handles routing, rate limiting, and authentication.
"""
from fastapi import FastAPI, Depends, Request, HTTPException, status, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
import httpx
from typing import Dict, Any
import time
import uuid
import websockets

from middleware.auth import get_current_user, get_optional_user
from middleware.rate_limiter import check_user_rate_limit, check_global_rate_limit
from utils import make_service_request
from config import settings
from shared.database.redis_client import redis_client
from shared.middleware.error_handler import register_exception_handlers
from shared.logging.logger import get_logger

logger = get_logger(settings.service_name, settings.log_level)

# Maximum request size: 50MB (for file uploads)
MAX_REQUEST_SIZE = settings.max_file_size_mb * 1024 * 1024


# Request/Response Logging Middleware with Correlation IDs
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all incoming requests and responses with correlation IDs."""
    
    async def dispatch(self, request: StarletteRequest, call_next):
        """Log request details and response status."""
        # Start timer
        start_time = time.time()
        
        # Generate or extract correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Add correlation ID to request state for downstream services
        request.state.correlation_id = correlation_id
        
        client_ip = request.client.host if request.client else "unknown"
        
        # Check request size for file uploads
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > MAX_REQUEST_SIZE:
                    logger.warning(
                        f"Request size {size} exceeds maximum {MAX_REQUEST_SIZE}",
                        extra={"correlation_id": correlation_id, "size": size}
                    )
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Request size exceeds maximum of {settings.max_file_size_mb}MB"
                    )
            except ValueError:
                pass  # Invalid content-length header, ignore
        
        # Log incoming request
        logger.info(
            f"-> Incoming request: {request.method} {request.url.path}",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": client_ip,
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            # Log response
            logger.info(
                f"<- Response: {response.status_code} | {duration:.3f}s",
                extra={
                    "correlation_id": correlation_id,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                    "path": request.url.path
                }
            )
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            # Calculate duration even on error
            duration = time.time() - start_time
            
            # Log error
            correlation_id = getattr(request.state, "correlation_id", "unknown")
            logger.error(
                f"[X] Request failed: {str(e)} | {duration:.3f}s",
                extra={
                    "correlation_id": correlation_id,
                    "error": str(e),
                    "duration_ms": round(duration * 1000, 2),
                    "path": request.url.path
                }
            )
            raise


# Create FastAPI app
app = FastAPI(
    title="RAG Edtech - API Gateway",
    description="Main API Gateway for RAG Edtech Platform",
    version="1.0.0"
)

# Add CORS middleware FIRST (must be before other middleware)
from shared.middleware.cors_config import configure_cors
configure_cors(app, settings.cors_origins)

# Add request logging middleware (after CORS)
app.add_middleware(RequestLoggingMiddleware)

# Register exception handlers
register_exception_handlers(app)


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup."""
    logger.info("Starting API Gateway...")
    
    # Connect to Redis
    if settings.redis_url:
        await redis_client.connect(settings.redis_url)
    
    logger.info("API Gateway started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down API Gateway...")
    if settings.redis_url:
        await redis_client.disconnect()
    logger.info("API Gateway shut down successfully")


@app.get("/health")
async def health_check():
    """Aggregate health check for all services."""
    health_status = {
        "status": "healthy",
        "service": "api-gateway"
    }
    
    if settings.redis_url:
        redis_healthy = await redis_client.health_check()
        health_status["redis"] = "connected" if redis_healthy else "disconnected"
    
    # Check downstream services
    services = {
        "auth": settings.auth_service_url,
        "document-processor": settings.document_processor_url,
        "rag-query": settings.rag_query_service_url,
        "analytics": settings.analytics_service_url
    }
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for service_name, service_url in services.items():
            if service_url:
                try:
                    response = await client.get(f"{service_url}/health")
                    health_status[service_name] = "healthy" if response.status_code == 200 else "unhealthy"
                except Exception:
                    health_status[service_name] = "unreachable"
    
    return health_status


# ============================================================================
# Auth Service Routes
# ============================================================================

@app.post("/api/auth/register")
async def register(request: Request):
    """Forward registration request to auth service."""
    await check_global_rate_limit(
        settings.rate_limit_global,
        settings.rate_limit_window_hours
    )
    
    body = await request.json()
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await make_service_request(
            client, "POST", f"{settings.auth_service_url}/auth/register",
            request, json=body
        )
        if response.status_code != 201:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()


@app.post("/api/auth/login")
async def login(request: Request):
    """Forward login request to auth service."""
    await check_global_rate_limit(
        settings.rate_limit_global,
        settings.rate_limit_window_hours
    )
    
    body = await request.json()
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await make_service_request(
            client, "POST", f"{settings.auth_service_url}/auth/login",
            request, json=body
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()


@app.post("/api/auth/refresh")
async def refresh_token(request: Request):
    """Forward token refresh request to auth service."""
    body = await request.json()
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await make_service_request(
            client, "POST", f"{settings.auth_service_url}/auth/refresh",
            request, json=body
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()


@app.patch("/api/auth/profile")
async def api_update_profile(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Forward profile update to auth service."""
    body = await request.json()
    
    # Get Authorization header from request
    auth_header = request.headers.get("authorization", "")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await make_service_request(
            client, "PATCH", f"{settings.auth_service_url}/auth/profile",
            request, json=body, headers={"Authorization": auth_header}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()


@app.post("/api/auth/change-password")
async def api_change_password(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Forward password change to auth service."""
    body = await request.json()
    
    # Get Authorization header from request
    auth_header = request.headers.get("authorization", "")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await make_service_request(
            client, "POST", f"{settings.auth_service_url}/auth/change-password",
            request, json=body, headers={"Authorization": auth_header}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

@app.get("/api/auth/me")
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information."""
    return current_user


# ============================================================================
# Document Processing Routes
# ============================================================================

@app.post("/api/content/upload")
async def upload_content(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Upload educational content.
    Rate limited per user.
    """
    # Check rate limits
    await check_user_rate_limit(
        current_user['user_id'],
        settings.rate_limit_per_user,
        settings.rate_limit_window_hours
    )
    await check_global_rate_limit(
        settings.rate_limit_global,
        settings.rate_limit_window_hours
    )
    
    # Get form data
    form = await request.form()
    
    # Forward to document processor
    async with httpx.AsyncClient(timeout=300.0) as client:
        files = {}
        data = {"user_id": current_user['user_id']}
        
        for key, value in form.items():
            if hasattr(value, 'file'):
                # It's a file
                files[key] = (value.filename, value.file, value.content_type)
            else:
                # It's form data
                data[key] = value
        
        response = await make_service_request(
            client, "POST", f"{settings.document_processor_url}/api/content/upload",
            request, files=files, data=data
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()


# ============================================================================
# RAG Query Routes
# ============================================================================

@app.post("/api/content/{content_id}/question")
async def ask_question(
    content_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Ask a question about specific content.
    Returns streaming response.
    """
    # Check rate limits
    await check_user_rate_limit(
        current_user['user_id'],
        settings.rate_limit_per_user,
        settings.rate_limit_window_hours
    )
    await check_global_rate_limit(
        settings.rate_limit_global,
        settings.rate_limit_window_hours
    )
    
    body = await request.json()
    body['user_id'] = current_user['user_id']
    
    # Forward to RAG query service with streaming
    async def stream_response():
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{settings.rag_query_service_url}/api/query/{content_id}",
                json=body
            ) as response:
                async for chunk in response.aiter_bytes():
                    yield chunk
    
    return StreamingResponse(stream_response(), media_type="text/event-stream")


# ============================================================================
# Analytics Routes
# ============================================================================

@app.get("/api/analytics/student/{student_id}")
async def get_student_analytics(
    student_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get learning analytics for a student."""
    # Students can only view their own analytics, teachers can view any
    if current_user['role'] != 'teacher' and current_user['user_id'] != student_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.analytics_service_url}/api/analytics/student/{student_id}"
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()


@app.get("/api/content/{content_id}/questions")
async def get_content_questions(
    content_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all questions asked about specific content."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.analytics_service_url}/api/content/{content_id}/questions"
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()


@app.get("/api/content/user/{user_id}")
async def get_user_documents(
    user_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user's documents with filtering."""
    # Forward query params
    query_params = str(request.url.query)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.document_processor_url}/api/content/user/{user_id}?{query_params}"
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()


@app.get("/api/prompts/document/{content_id}")
async def get_document_prompts(
    content_id: str,
    current_user: Dict[str, Any] = Depends(get_optional_user)
):
    """Get suggested questions for a document."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.document_processor_url}/api/prompts/document/{content_id}"
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()


@app.get("/api/prompts/global")
async def get_global_prompts(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get global chat suggested questions."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.document_processor_url}/api/prompts/global?user_id={user_id}"
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()


@app.post("/api/content/{content_id}/question")
async def document_chat_stream(
    content_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Document chat with streaming response."""
    body = await request.json()
    
    # Forward streaming response
    async def stream_response():
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{settings.rag_query_url}/api/content/{content_id}/question",
                json=body
            ) as response:
                async for chunk in response.aiter_bytes():
                    yield chunk
    
    return StreamingResponse(stream_response(), media_type="text/plain")


@app.post("/api/query/{content_id}/complete")
async def document_chat_complete(
    content_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Document-specific chat with sources."""
    body = await request.json()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.rag_query_service_url}/api/query/{content_id}/complete",
            json=body
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()


@app.post("/api/query/global/complete")
async def global_chat_complete(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Global chat across multiple documents."""
    body = await request.json()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.rag_query_service_url}/api/query/global/complete",
            json=body
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()


@app.get("/api/analytics/teacher/students")
async def get_teacher_students(
    teacher_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all students activity for teacher."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.analytics_service_url}/api/analytics/teacher/students?teacher_id={teacher_id}"
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()


@app.get("/api/analytics/teacher/overview")
async def get_teacher_overview(
    teacher_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get teacher dashboard overview."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.analytics_service_url}/api/analytics/teacher/overview?teacher_id={teacher_id}"
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()


@app.websocket("/ws/document/{content_id}/status")
async def websocket_proxy(websocket: WebSocket, content_id: str):
    """
    WebSocket proxy for document processing status updates.
    Forwards connection to document-processor service.
    """
    await websocket.accept()
    
    # Connect to backend WebSocket
    backend_ws_url = f"ws://{settings.document_processor_url.split('//')[1]}/ws/document/{content_id}/status"
    
    try:
        async with websockets.connect(backend_ws_url) as backend_ws:
            # Proxy messages in both directions
            async def forward_from_backend():
                async for message in backend_ws:
                    await websocket.send_text(message)
            
            async def forward_from_client():
                try:
                    while True:
                        data = await websocket.receive_text()
                        await backend_ws.send(data)
                except Exception:
                    pass
            
            # Run both tasks concurrently
            import asyncio
            await asyncio.gather(
                forward_from_backend(),
                forward_from_client(),
                return_exceptions=True
            )
    
    except Exception as e:
        logger.error(f"WebSocket proxy error: {e}")
        try:
            await websocket.close()
        except:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

