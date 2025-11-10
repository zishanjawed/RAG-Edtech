# RAG Edtech Backend Services

**Microservices backend architecture for AI-powered educational platform**

> Six independent FastAPI services with shared utilities, designed for scalability, fault isolation, and production deployment.

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0-green.svg)](https://www.mongodb.com/)
[![Redis](https://img.shields.io/badge/Redis-7.2-red.svg)](https://redis.io/)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3.12-orange.svg)](https://www.rabbitmq.com/)

---

## Architecture Overview

### Microservices Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        API Gateway (8000)                         │
│  Entry Point | Rate Limiting | JWT Middleware | Request Routing  │
└────┬─────────┬──────────┬──────────┬───────────┬─────────────────┘
     │         │          │          │           │
     ▼         ▼          ▼          ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐
│  Auth   │ │Document │ │  Vector │ │   RAG   │ │  Analytics  │
│ Service │ │Processor│ │ Service │ │  Query  │ │   Service   │
│  8001   │ │  8002   │ │  8003   │ │  8004   │ │    8005     │
└────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └──────┬──────┘
     │           │           │           │             │
     └───────────┴───────────┴───────────┴─────────────┘
                     │           │           │
                     ▼           ▼           ▼
        ┌────────────────────────────────────────┐
        │         Infrastructure Layer            │
        │                                          │
        │  MongoDB    - User data, content,       │
        │              analytics                   │
        │  Pinecone   - Vector embeddings         │
        │  Redis      - Caching, rate limiting    │
        │  RabbitMQ   - Async message queue       │
        │  Langfuse   - LLM observability         │
        │                                          │
        └────────────────────────────────────────┘
```

### Service Communication

**Synchronous (HTTP):**
- Frontend → API Gateway → Specific Service
- Service-to-service HTTP calls (rare, mostly async)

**Asynchronous (RabbitMQ):**
- Document Processor → RabbitMQ → Vectorization Service
- Event-driven processing for expensive operations

**Caching (Redis):**
- RAG responses cached for 1 hour
- Analytics cached for 5 minutes
- Rate limiting state

---

## Services Overview

### 1. API Gateway (Port 8000)

**Location:** `services/api-gateway/`

**Purpose:** Single entry point for all client requests

**Key Responsibilities:**
- Route requests to appropriate microservices
- JWT authentication middleware (validates tokens)
- Rate limiting (100 req/hour per user, Redis-based)
- CORS configuration (centralized)
- Health check aggregation
- Request correlation IDs

**Technology Stack:**
- FastAPI
- Redis (rate limiting)
- HTTP client for service routing

**Key Files:**
- `main.py` - FastAPI app with routing logic
- `middleware/rate_limiter.py` - Redis sliding window rate limiting
- `middleware/auth_middleware.py` - JWT validation
- `utils.py` - Service health checks

**API Endpoints:**
- `GET /health` - Aggregate health of all services
- `/*` - Proxy to downstream services

**Configuration:**
```env
RATE_LIMIT_PER_USER=100
RATE_LIMIT_WINDOW_SECONDS=3600
CORS_ORIGINS=http://localhost:3000
```

---

### 2. Auth Service (Port 8001)

**Location:** `services/auth/`

**Purpose:** User authentication and authorization

**Key Responsibilities:**
- User registration with validation
- Login with JWT token generation
- Token refresh mechanism
- Password hashing (bcrypt, 12 rounds)
- Role-based access control (student/teacher)

**Technology Stack:**
- FastAPI
- MongoDB (users collection)
- bcrypt (password hashing)
- PyJWT (token generation)

**Key Files:**
- `main.py` - Auth endpoints
- `models/user.py` - User data models
- `security/jwt_handler.py` - JWT operations
- `security/password.py` - Password hashing/verification

**API Endpoints:**
- `POST /api/auth/register` - Create new user
- `POST /api/auth/login` - Authenticate and get tokens
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user info

**Database Schema (MongoDB):**
```javascript
users: {
  _id: ObjectId,
  user_id: String (UUID),
  email: String (unique),
  password_hash: String,
  full_name: String,
  role: String ("student" | "teacher"),
  is_active: Boolean,
  created_at: DateTime,
  last_login: DateTime
}
```

**JWT Token Structure:**
```javascript
{
  "sub": "user_id",           // User ID
  "email": "user@example.com",
  "role": "student",
  "exp": 1234567890,          // Expiry (15 min for access, 7 days for refresh)
  "iat": 1234567890,          // Issued at
  "type": "access" | "refresh"
}
```

---

### 3. Document Processor (Port 8002)

**Location:** `services/document-processor/`

**Purpose:** Document upload, parsing, and chunking

**Key Responsibilities:**
- Handle document uploads (PDF, MD, TXT, DOCX)
- Extract text with Docling (PDF) or basic parsers
- Generate SHA-256 content hash for deduplication
- Hierarchical chunking (512 tokens, 50 overlap)
- Publish chunks to RabbitMQ for vectorization
- WebSocket status updates for real-time feedback
- LLM-generated suggested questions (GPT-4o-mini)
- Document deletion with complete cleanup

**Technology Stack:**
- FastAPI
- Docling (PDF parsing)
- PyPDF2 (fallback PDF parser)
- python-docx (DOCX parsing)
- MongoDB (content collection)
- RabbitMQ (publisher)
- WebSocket (real-time updates)
- Redis (pubsub for status updates)

**Key Files:**
- `main.py` - Upload, list, delete endpoints
- `parsers/docling_parser.py` - Docling integration
- `parsers/basic_parser.py` - Fallback parsers
- `chunking/hierarchical_chunker.py` - Token-based chunking
- `publisher/rabbitmq_publisher.py` - Message queue publisher
- `websocket_handler.py` - WebSocket connections
- `question_generator.py` - LLM question generation
- `deletion_service.py` - Complete document cleanup

**API Endpoints:**
- `POST /api/content/upload` - Upload document
- `GET /api/content/{content_id}` - Get document details
- `GET /api/content/user/{user_id}` - List user documents (with filters)
- `DELETE /api/content/{content_id}` - Delete document
- `GET /api/prompts/document/{content_id}` - Get suggested questions
- `GET /api/prompts/global` - Get cross-document questions
- `WS /ws/document/{content_id}/status` - Real-time status updates

**Database Schema (MongoDB):**
```javascript
content: {
  _id: ObjectId,
  content_id: String (UUID),
  user_id: String (UUID),          // Current owner
  filename: String,
  file_type: String,
  title: String,
  subject: String,
  grade_level: String,
  tags: Array<String>,              // NEW: Custom tags
  status: String,                   // "processing" | "completed" | "failed"
  total_chunks: Number,
  processed_chunks: Number,
  
  // Deduplication & Traceability
  content_hash: String,             // SHA-256 hash
  is_duplicate: Boolean,
  original_uploader_id: String,
  original_upload_date: DateTime,
  upload_history: Array<{
    user_id: String,
    user_name: String,
    upload_date: DateTime,
    filename: String,
    content_hash: String
  }>,
  
  metadata: Object,
  created_at: DateTime,
  updated_at: DateTime
}

suggested_questions: {
  _id: ObjectId,
  content_id: String (UUID),        // null for global questions
  user_id: String (UUID),           // For global questions
  questions: Array<{
    id: String,
    text: String,
    category: String,
    difficulty: String,
    icon: String
  }>,
  created_at: DateTime,
  expires_at: DateTime
}
```

**Deduplication Flow:**
1. Calculate SHA-256 hash of normalized content
2. Query MongoDB for existing content_hash
3. If found: Return existing content_id, add to upload_history
4. If new: Process normally, save new content_hash

**Deletion Flow:**
1. Verify permissions (owner, teacher, or in upload_history)
2. Delete MongoDB content record
3. Delete Pinecone namespace (all vectors)
4. Delete physical file from uploads/
5. Clear Redis cache entries
6. Return deletion stats

---

### 4. Vectorization Service (Port 8003)

**Location:** `services/vectorization/`

**Purpose:** Generate embeddings and store in vector database

**Key Responsibilities:**
- Consume chunks from RabbitMQ queue
- Generate embeddings using OpenAI (text-embedding-3-large)
- Batch processing (up to 100 chunks)
- Store vectors in Pinecone with metadata
- Update MongoDB with processing progress
- Error handling with retries (3 attempts)

**Technology Stack:**
- FastAPI (minimal, mostly worker)
- RabbitMQ (consumer)
- OpenAI API (embeddings)
- Pinecone (vector storage)
- MongoDB (progress tracking)

**Key Files:**
- `main.py` - Service initialization
- `workers/embedding_worker.py` - RabbitMQ consumer
- `embeddings/openai_embeddings.py` - OpenAI API client
- `vector_store/pinecone_client.py` - Pinecone operations

**Processing Flow:**
1. Consume message from RabbitMQ (chunk data)
2. Generate embedding (3072 dimensions)
3. Store in Pinecone with metadata:
   ```python
   {
     "content_id": str,
     "chunk_id": str,
     "chunk_index": int,
     "text": str (max 40,000 chars),
     "token_count": int,
     "subject": str,
     "grade_level": str,
     "document_title": str,
     "uploader_name": str,
     "uploader_id": str,
     "upload_date": str (ISO format)
   }
   ```
4. Update MongoDB: increment processed_chunks (atomic)
5. If all chunks processed: set status = "completed"
6. Publish status update to Redis pubsub
7. Acknowledge RabbitMQ message

**Embedding Model:**
- Model: `text-embedding-3-large`
- Dimensions: 3072
- Cost: $0.00013 per 1K tokens
- Batch size: 100 chunks per API call

**Error Handling:**
- Retry failed embeddings 3 times with exponential backoff
- Dead letter queue for permanent failures
- Log errors to observability platform

---

### 5. RAG Query Service (Port 8004)

**Location:** `services/rag-query/`

**Purpose:** Question answering with retrieval-augmented generation

**Key Responsibilities:**
- Semantic search via Pinecone
- GPT-4 answer generation with streaming
- Redis caching (90%+ hit rate, 1 hour TTL)
- Prompt injection prevention
- Question classification (6 types)
- Source attribution
- Global chat across multiple documents
- Langfuse observability integration

**Technology Stack:**
- FastAPI
- Pinecone (semantic search)
- OpenAI GPT-4 (answer generation)
- Redis (response caching)
- MongoDB (question storage)
- Langfuse (LLM tracing)

**Key Files:**
- `main.py` - Query endpoints
- `pipeline/rag_pipeline.py` - Complete RAG flow
- `retrieval/pinecone_retriever.py` - Semantic search
- `llm/openai_client.py` - GPT-4 streaming
- `cache/redis_cache.py` - Response caching
- `security/prompt_injection.py` - Security checks
- `prompts/educational_prompts.py` - System prompts
- `access_control.py` - Document access helper

**API Endpoints:**
- `POST /api/content/{content_id}/question` - Ask question (streaming)
- `POST /api/query/{content_id}/complete` - Ask with sources (non-streaming)
- `POST /api/query/global/complete` - Global chat across documents
- `GET /api/content/{content_id}/questions` - Question history

**RAG Pipeline (3-5 seconds):**
```
1. Validate input (length, prompt injection)
2. Check Redis cache (MD5 hash key)
3. If cache miss:
   a. Generate query embedding (500ms)
   b. Semantic search in Pinecone (100ms, top-5)
   c. Construct prompt with context
   d. Stream GPT-4 response (2-5s)
   e. Cache response in Redis
   f. Store Q&A in MongoDB
   g. Track with Langfuse
```

**Semantic Search (Pinecone):**
```python
query_params = {
  "vector": embedding_vector,      # 3072 dimensions
  "top_k": 5,                      # Return top 5 chunks
  "include_metadata": True,
  "filter": {
    "content_id": {"$eq": content_id}  # Filter by document
  }
}
```

**Global Search:**
```python
# Search across all user-accessible documents
query_params = {
  "vector": embedding_vector,
  "top_k": 8,                      # More results for diversity
  "include_metadata": True,
  "filter": {
    "content_id": {"$in": accessible_doc_ids}  # User's documents
  }
}
# Post-process: Max 2 chunks per document
```

**System Prompt:**
```
You are an expert IB Chemistry tutor providing detailed, scientifically 
accurate explanations suitable for IB Diploma students (ages 16-18).

Guidelines:
1. Base your answers ONLY on the provided context
2. Use appropriate scientific terminology
3. Provide step-by-step explanations when appropriate
4. If context doesn't contain relevant information, say so clearly
5. Be concise but thorough
6. Cite sources by document title and uploader

Format your response in clear, readable markdown.
```

**Question Classification:**
- Definition: "What is X?"
- Explanation: "Why does X happen?"
- Comparison: "Difference between X and Y?"
- Procedure: "How to calculate X?"
- Application: "Apply X to Y"
- Evaluation: "Analyze X"

**Database Schema (MongoDB):**
```javascript
questions: {
  _id: ObjectId,
  question_id: String (UUID),
  content_id: String (UUID) | null,  // null for global
  user_id: String (UUID),
  question: String,
  answer: String,
  question_type: String,
  sources: Array<{
    source_id: Number,
    document_title: String,
    uploader_name: String,
    uploader_id: String,
    upload_date: String,
    chunk_index: Number,
    similarity_score: Number
  }>,
  is_global: Boolean,                // NEW: Global chat flag
  searched_doc_ids: Array<String>,   // NEW: Docs searched
  documents_searched: Number,        // NEW: Count
  tokens_used: Number,
  response_time_ms: Number,
  langfuse_trace_id: String,
  cached: Boolean,
  created_at: DateTime
}
```

**Access Control (Global Chat):**
```python
def get_user_accessible_docs(user_id, role):
  if role == "teacher":
    # Teachers can access ALL documents
    return db.content.find({})
  else:
    # Students: owned + in upload_history + shared
    return db.content.find({
      "$or": [
        {"user_id": user_id},
        {"original_uploader_id": user_id},
        {"upload_history.user_id": user_id}
      ]
    })
```

**Performance Optimization:**
- Cache hit rate: 90%+ (1 hour TTL)
- Cache hit response: 50ms
- Cache miss response: 3000ms
- Cost per cached query: $0
- Cost per uncached query: $0.02-0.05

---

### 6. Analytics Service (Port 8005)

**Location:** `services/analytics/`

**Purpose:** Student engagement metrics and teacher dashboards

**Key Responsibilities:**
- Student engagement metrics (questions, activity)
- Content usage analytics
- Teacher dashboard data (class-wide)
- MongoDB aggregation pipelines
- Redis caching (5 minute TTL)
- NLP analysis (question sentiment, complexity)

**Technology Stack:**
- FastAPI
- MongoDB (aggregations)
- Redis (caching)
- NLTK (NLP analysis)

**Key Files:**
- `main.py` - Analytics endpoints
- `aggregations/student_analytics.py` - Student metrics
- `aggregations/content_analytics.py` - Content metrics
- `aggregations/teacher_analytics.py` - Teacher dashboard
- `cache/analytics_cache.py` - Result caching
- `nlp/text_analysis.py` - NLP utilities

**API Endpoints:**
- `GET /api/analytics/student/{student_id}` - Student engagement
- `GET /api/analytics/content/{content_id}` - Content usage
- `GET /api/analytics/teacher/dashboard` - Teacher overview
- `GET /api/analytics/student/{student_id}/activity` - Activity timeline

**Metrics Tracked:**
- Total questions asked per student
- Questions in last 7 days
- Average response time
- Total tokens used
- Top content by questions
- Daily/weekly activity trends
- Question type distribution
- Student engagement scores

**Example Aggregation (Student Metrics):**
```python
pipeline = [
  {"$match": {"user_id": student_id}},
  {"$group": {
    "_id": "$user_id",
    "total_questions": {"$sum": 1},
    "avg_response_time": {"$avg": "$response_time_ms"},
    "total_tokens": {"$sum": "$tokens_used"}
  }},
  {"$lookup": {
    "from": "content",
    "localField": "content_id",
    "foreignField": "content_id",
    "as": "content_info"
  }}
]
```

**Caching Strategy:**
```python
cache_key = f"analytics:student:{student_id}"
ttl = 300  # 5 minutes

# Check cache first
cached = redis.get(cache_key)
if cached:
  return json.loads(cached)

# Compute and cache
result = compute_analytics()
redis.setex(cache_key, ttl, json.dumps(result))
return result
```

---

## Shared Module

**Location:** `shared/`

The `shared/` directory contains utilities used across all services:

### Directory Structure

```
shared/
├── config/
│   ├── __init__.py
│   └── settings.py              # Centralized configuration
│
├── database/
│   ├── __init__.py
│   ├── mongodb_client.py        # MongoDB connection pool
│   └── redis_client.py          # Redis connection pool
│
├── exceptions/
│   ├── __init__.py
│   └── custom_exceptions.py     # Custom exception classes
│
├── logging/
│   ├── __init__.py
│   └── logger.py                # Structured logging setup
│
├── middleware/
│   ├── __init__.py
│   ├── cors_config.py           # Centralized CORS (NEW)
│   └── error_handler.py         # Global error handling
│
├── observability/
│   ├── __init__.py
│   └── langfuse_client.py       # Langfuse LLM tracing
│
└── utils/
    ├── __init__.py
    ├── content_hash.py          # SHA-256 hashing (NEW)
    ├── retry.py                 # Retry logic with backoff
    └── security.py              # Security utilities
```

### Key Components

**1. Configuration Management**
```python
# shared/config/settings.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Database
    MONGO_HOST: str = "mongodb"
    MONGO_PORT: int = 27017
    MONGO_USERNAME: str
    MONGO_PASSWORD: str
    
    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    
    # OpenAI
    OPENAI_API_KEY: str
    
    # JWT
    JWT_SECRET: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    
    class Config:
        env_file = ".env"
```

**2. MongoDB Client**
```python
# shared/database/mongodb_client.py
from motor.motor_asyncio import AsyncIOMotorClient

class MongoDBClient:
    client: AsyncIOMotorClient = None
    
    async def connect(self):
        self.client = AsyncIOMotorClient(
            f"mongodb://{username}:{password}@{host}:{port}"
        )
    
    async def disconnect(self):
        self.client.close()
    
    def get_database(self, name: str):
        return self.client[name]
```

**3. Centralized CORS (NEW)**
```python
# shared/middleware/cors_config.py
from fastapi.middleware.cors import CORSMiddleware

def configure_cors(app, allowed_origins: list[str]):
    """
    Centralized CORS configuration for all services.
    Automatically allows ALL localhost/127.0.0.1 ports.
    """
    def is_localhost_origin(origin: str) -> bool:
        return (
            origin.startswith("http://localhost") or
            origin.startswith("http://127.0.0.1") or
            origin.startswith("https://localhost")
        )
    
    def allow_origin(origin: str) -> bool:
        return origin in allowed_origins or is_localhost_origin(origin)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

**4. Content Hashing (NEW)**
```python
# shared/utils/content_hash.py
import hashlib

def generate_content_hash(text: str) -> str:
    """Generate SHA-256 hash for deduplication"""
    normalized = text.lower().strip()
    return hashlib.sha256(normalized.encode()).hexdigest()
```

**5. Retry Logic**
```python
# shared/utils/retry.py
import asyncio
from functools import wraps

def async_retry(max_attempts=3, delay=1, backoff=2):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    await asyncio.sleep(delay * (backoff ** attempt))
        return wrapper
    return decorator
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- OpenAI API key
- Pinecone API key (with index created)

### Installation

```bash
# 1. Navigate to project root
cd RAG-Edtech

# 2. Create virtual environment (optional)
python -m venv venv
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Start infrastructure
docker-compose up -d mongodb redis rabbitmq

# 6. Verify infrastructure
docker-compose ps

# 7. Start all services
docker-compose up -d

# 8. Check service health
curl http://localhost:8000/health
```

### Running Individual Services (Development)

```bash
# Terminal 1: Auth Service
cd services/auth
uvicorn main:app --reload --port 8001

# Terminal 2: Document Processor
cd services/document-processor
uvicorn main:app --reload --port 8002

# Terminal 3: RAG Query
cd services/rag-query
uvicorn main:app --reload --port 8004

# Terminal 4: Vectorization Worker
cd services/vectorization
python main.py

# Terminal 5: Analytics
cd services/analytics
uvicorn main:app --reload --port 8005
```

---

## API Reference (High-Level)

### Authentication

- `POST /api/auth/register` - Create account
- `POST /api/auth/login` - Get JWT tokens
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Current user info

### Document Management

- `POST /api/content/upload` - Upload document
- `GET /api/content/{content_id}` - Document details
- `GET /api/content/user/{user_id}` - List documents (with filters)
- `DELETE /api/content/{content_id}` - Delete document
- `GET /api/prompts/document/{id}` - Suggested questions
- `WS /ws/document/{id}/status` - Real-time status

### Question Answering

- `POST /api/content/{id}/question` - Document chat (streaming)
- `POST /api/query/{id}/complete` - With sources (non-streaming)
- `POST /api/query/global/complete` - Global chat
- `GET /api/content/{id}/questions` - Question history

### Analytics

- `GET /api/analytics/student/{id}` - Student metrics
- `GET /api/analytics/content/{id}` - Content usage
- `GET /api/analytics/teacher/dashboard` - Teacher overview

---

## Development Workflow

### 1. Adding a New Endpoint

```python
# Define Pydantic models
from pydantic import BaseModel

class MyRequest(BaseModel):
    field1: str
    field2: int

# Add route to service main.py
@app.post("/api/my-endpoint")
async def my_endpoint(request: MyRequest):
    result = await process_request(request)
    return {"result": "success"}

# Implement business logic
async def process_request(request: MyRequest):
    # Implementation
    pass

# Add unit tests (tests/test_my_endpoint.py)
@pytest.mark.asyncio
async def test_my_endpoint():
    response = await client.post("/api/my-endpoint", json={
        "field1": "value",
        "field2": 123
    })
    assert response.status_code == 200
```

### 2. Adding Database Operations

```python
# Use shared MongoDB client
from shared.database.mongodb_client import get_database

db = get_database("rag_edtech")
collection = db["my_collection"]

# Create index
await collection.create_index("field_name", unique=True)

# Insert document
await collection.insert_one({
    "field1": "value",
    "created_at": datetime.utcnow()
})

# Query documents
results = await collection.find({"field1": "value"}).to_list(length=100)
```

### 3. Adding to Shared Module

```python
# Create utility in shared/utils/my_util.py
def my_utility_function(arg: str) -> str:
    """Utility description"""
    return arg.upper()

# Export from shared/__init__.py
from .utils.my_util import my_utility_function

# Use in any service
from shared import my_utility_function

result = my_utility_function("test")
```

### 4. Debugging

```python
# Add structured logging
import logging
logger = logging.getLogger(__name__)

logger.debug(f"Debug info: {variable}")
logger.info(f"Processing request: {request_id}")
logger.error(f"Error occurred: {error}", exc_info=True)

# View logs
docker-compose logs -f rag-query

# Interactive debugging (iPython)
import IPython; IPython.embed()
```

### 5. Testing

```bash
# Run all tests
pytest

# Run specific service tests
pytest services/auth/tests/ -v

# Run with coverage
pytest --cov=services --cov=shared --cov-report=html

# Run integration tests only
pytest tests/integration/ -v

# Run with specific markers
pytest -m "not slow"
```

---

## Infrastructure Setup

### MongoDB

```bash
# Access MongoDB shell
docker exec -it rag-edtech-mongodb-1 mongosh -u admin -p password123

# Use database
use rag_edtech

# List collections
show collections

# Query users
db.users.find()

# Query content
db.content.find().limit(5)

# Create index
db.content.createIndex({"content_hash": 1})

# Check indexes
db.content.getIndexes()
```

### Redis

```bash
# Access Redis CLI
docker exec -it rag-edtech-redis-1 redis-cli

# Check connection
PING

# List all keys
KEYS *

# Get cached response
GET rag:cache:abc123

# Check TTL
TTL rag:cache:abc123

# Clear all cache (WARNING: Development only!)
FLUSHALL
```

### RabbitMQ

```bash
# Access management UI
open http://localhost:15672
# Login: admin / password123

# Check queue status
# Navigate to "Queues" tab

# Purge queue (dev only)
# Click on queue → "Purge Messages"

# Monitor message rate
# See "Message rates" graph

# CLI operations
docker exec -it rag-edtech-rabbitmq-1 rabbitmqctl list_queues
```

### Pinecone

```python
# Create index (one-time setup)
import pinecone

pinecone.init(api_key=PINECONE_API_KEY)

pinecone.create_index(
    name="edtech-rag-index",
    dimension=3072,
    metric="cosine",
    pod_type="serverless"
)

# Query vectors
import pinecone

index = pinecone.Index("edtech-rag-index")

# Stats
stats = index.describe_index_stats()
print(f"Total vectors: {stats['total_vector_count']}")

# Search
results = index.query(
    vector=[0.1] * 3072,
    top_k=5,
    include_metadata=True
)
```

---

## Testing Strategy

### Unit Tests (75%+ Coverage)

Each service has unit tests in `tests/` directory:

```bash
services/
├── auth/tests/
│   ├── test_auth_service.py
│   ├── test_jwt_handler.py
│   └── test_password.py
│
├── document-processor/tests/
│   ├── test_upload.py
│   ├── test_parsers.py
│   └── test_chunking.py
│
├── rag-query/tests/
│   ├── test_rag_pipeline.py
│   ├── test_cache.py
│   └── test_security.py
│
└── analytics/tests/
    └── test_aggregations.py
```

**Example Test:**
```python
import pytest
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_login_success(test_client):
    """Test successful login"""
    response = await test_client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "TestPass@123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "test@example.com"
```

### Integration Tests

**Location:** `tests/integration/`

```python
@pytest.mark.asyncio
async def test_rag_pipeline_end_to_end():
    """Test complete RAG flow"""
    
    # 1. Upload document
    upload_response = await client.post(
        "/api/content/upload",
        files={"file": ("test.pdf", pdf_content)},
        data={"user_id": user_id}
    )
    content_id = upload_response.json()["content_id"]
    
    # 2. Wait for processing
    await asyncio.sleep(30)
    
    # 3. Ask question
    question_response = await client.post(
        f"/api/content/{content_id}/question",
        json={
            "question": "What is the main topic?",
            "user_id": user_id
        }
    )
    
    assert question_response.status_code == 200
    assert len(question_response.text) > 0
```

### Load Testing

```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load/test_rag_query.py --host http://localhost:8000

# Access UI
open http://localhost:8089
```

---

## Deployment

### Development (Docker Compose)

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Restart service
docker-compose restart rag-query

# Stop all
docker-compose down

# Remove volumes (WARNING: Deletes data)
docker-compose down -v
```

### Production Checklist

- [ ] Set strong JWT_SECRET (min 32 characters)
- [ ] Use production MongoDB with replica set
- [ ] Configure Redis persistence (AOF + RDB)
- [ ] Set up RabbitMQ cluster with mirrored queues
- [ ] Enable HTTPS with Let's Encrypt
- [ ] Configure rate limits appropriately
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Enable log aggregation (ELK stack)
- [ ] Configure automated backups (MongoDB, Redis)
- [ ] Set up alerts for service health
- [ ] Use environment-specific .env files
- [ ] Enable Langfuse for LLM cost tracking

### Production Deployment (AWS EC2)

**See [PROJECT_MASTER.md](../PROJECT_MASTER.md) § Deployment → Production Deployment for complete guide**

**Quick Overview:**
1. Launch EC2 instance (t3.medium, Ubuntu 22.04)
2. Install Docker and Docker Compose
3. Clone repository and configure `.env`
4. Start services: `docker-compose up -d`
5. Configure Nginx reverse proxy
6. Set up SSL with Let's Encrypt
7. Configure firewall (UFW)
8. Enable auto-start with systemd

---

## Troubleshooting

### Service Won't Start

```bash
# Check if port is in use
lsof -i :8000

# Kill process
kill -9 <PID>

# Check Docker logs
docker-compose logs service-name

# Restart service
docker-compose restart service-name

# Remove and recreate
docker-compose down
docker-compose up -d
```

### MongoDB Connection Failed

```bash
# Check MongoDB is running
docker-compose ps mongodb

# Check connection string in .env
MONGO_HOST=mongodb  # Should be 'mongodb' not 'localhost' in Docker

# Test connection
docker exec -it rag-edtech-mongodb-1 mongosh -u admin -p password123

# Restart MongoDB
docker-compose restart mongodb
```

### RabbitMQ Queue Issues

```bash
# Check queue status
open http://localhost:15672

# Check consumer count
# Should be 1 for vectorization_queue

# Restart vectorization service
docker-compose restart vectorization

# Purge stuck queue (dev only)
# Use RabbitMQ management UI

# Check logs
docker-compose logs -f vectorization
```

### Pinecone Connection Failed

```bash
# Verify API key
echo $PINECONE_API_KEY

# Check index exists
# Login to Pinecone dashboard

# Verify index dimensions (must be 3072)

# Test connection
python -c "import pinecone; pinecone.init(api_key='your-key'); print(pinecone.list_indexes())"
```

### High Memory Usage

```bash
# Check resource usage
docker stats

# Limit memory in docker-compose.yml
services:
  rag-query:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'

# Restart with limits
docker-compose down
docker-compose up -d
```

### Slow Performance

```bash
# Check MongoDB indexes
docker exec -it rag-edtech-mongodb-1 mongosh -u admin -p password123
> use rag_edtech
> db.content.getIndexes()

# Check Redis cache hit rate
docker exec -it rag-edtech-redis-1 redis-cli
> INFO stats
# Look for "keyspace_hits" and "keyspace_misses"

# Check Pinecone query latency
# Should be <100ms

# Enable query profiling in MongoDB
> db.setProfilingLevel(2)
> db.system.profile.find().sort({ts:-1}).limit(5)
```

---

## Monitoring & Observability

### Health Checks

```bash
# API Gateway
curl http://localhost:8000/health

# Individual services
curl http://localhost:8001/health  # Auth
curl http://localhost:8002/health  # Document Processor
curl http://localhost:8004/health  # RAG Query
curl http://localhost:8005/health  # Analytics
```

### Langfuse Integration

```python
# Track LLM calls
from langfuse import Langfuse

langfuse = Langfuse(
    public_key=LANGFUSE_PUBLIC_KEY,
    secret_key=LANGFUSE_SECRET_KEY
)

trace = langfuse.trace(
    name="rag_query",
    user_id=user_id,
    metadata={"content_id": content_id}
)

generation = trace.generation(
    name="gpt4_answer",
    model="gpt-4",
    input=prompt,
    output=answer,
    usage={
        "input_tokens": 1500,
        "output_tokens": 300,
        "total_cost": 0.045
    }
)
```

### Metrics to Track

- Request rate (per service)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Cache hit rate (Redis)
- Queue depth (RabbitMQ)
- Token usage (OpenAI)
- Cost per query
- Embedding generation time
- Database query time

---

## Security Best Practices

### Environment Variables

```bash
# Never commit .env to git
echo ".env" >> .gitignore

# Use strong secrets
JWT_SECRET=$(openssl rand -hex 32)

# Rotate secrets regularly
# Update JWT_SECRET every 90 days
```

### Rate Limiting

```python
# Configure per service
RATE_LIMIT_PER_USER=100  # requests per hour
RATE_LIMIT_WINDOW_SECONDS=3600

# Adjust for production
# API Gateway: 1000/hour
# RAG Query: 100/hour
# Upload: 50/hour
```

### Input Validation

```python
# Always use Pydantic models
from pydantic import BaseModel, Field, validator

class QuestionRequest(BaseModel):
    question: str = Field(max_length=500)
    user_id: str
    
    @validator('question')
    def validate_question(cls, v):
        if detect_prompt_injection(v):
            raise ValueError("Suspicious input detected")
        return v
```

### Authentication

```python
# Verify JWT in all protected endpoints
from fastapi import Depends, HTTPException
from jose import jwt, JWTError

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401)
        return user_id
    except JWTError:
        raise HTTPException(status_code=401)
```

---

## Quick References

- **Interactive API Docs:** http://localhost:8000/docs (Swagger UI with all endpoints)
- **RabbitMQ Management:** http://localhost:15672 (admin/password123)
- **Root README:** [../README.md](../README.md) - Full project documentation and setup

---

