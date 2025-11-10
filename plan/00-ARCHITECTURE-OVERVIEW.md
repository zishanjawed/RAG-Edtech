# RAG Edtech Platform - Architecture Overview

## System Architecture

This is a production-grade, scalable RAG-based educational platform built using microservices architecture.

### High-Level Architecture Diagram

```
┌-----------------------------------------------------------------┐
|                         API Gateway                              |
|         (Rate Limiting, Auth, Routing - Port 8000)              |
└-----------┬-----------------------------------------------------┘
            |
            ├------------------------------------------------------┐
            |                                                       |
    ┌-------▼------┐  ┌--------------┐  ┌----------------┐       |
    | Auth Service |  |   Document   |  |  RAG Query     |       |
    |   (JWT)      |  |  Processor   |  |  Service       |       |
    |              |  |  (Docling)   |  |  (Streaming)   |       |
    └--------------┘  └------┬-------┘  └----┬-----------┘       |
                             |               |                     |
                      ┌------▼------┐  ┌-----▼---------┐  ┌------▼--------┐
                      | Vectorization|  |   Analytics   |  |               |
                      |   Service    |  |   Service     |  |               |
                      |  (Embeddings)|  | (Aggregations)|  |               |
                      └--------------┘  └---------------┘  └---------------┘
                             |
                             |
    ┌------------------------┴---------------------------------------┐
    |                                                                 |
┌---▼--------┐  ┌----------┐  ┌---------┐  ┌----------┐  ┌----------┐
|  MongoDB   |  | Pinecone |  |  Redis  |  | RabbitMQ |  | Langfuse |
|            |  |  (Vector |  | (Cache) |  |  (Queue) |  |(Observ.) |
└------------┘  └----------┘  └---------┘  └----------┘  └----------┘
```

## Core Services

### 1. API Gateway Service
- **Port:** 8000
- **Responsibility:** Entry point, routing, rate limiting, authentication
- **Tech:** FastAPI, Redis
- **Key Features:**
  - Request routing to microservices
  - JWT validation middleware
  - Rate limiting (100 req/hour per user, 1000/hour global)
  - CORS configuration
  - Health check aggregation

### 2. Auth Service
- **Port:** 8001
- **Responsibility:** User authentication and authorization
- **Tech:** FastAPI, MongoDB, JWT, bcrypt
- **Key Features:**
  - User registration/login
  - JWT token generation (access + refresh)
  - Password hashing
  - Role-based access (student/teacher)

### 3. Document Processing Service
- **Port:** 8002
- **Responsibility:** Document upload, parsing, chunking
- **Tech:** FastAPI, Docling, RabbitMQ, MongoDB
- **Key Features:**
  - Multi-format support (PDF, MD, TXT)
  - Intelligent parsing with Docling
  - Hierarchical chunking (512 tokens, 50 overlap)
  - Metadata extraction
  - Async processing via message queue

### 4. Vectorization Service
- **Port:** 8003
- **Responsibility:** Generate embeddings, store in Pinecone
- **Tech:** FastAPI, OpenAI Embeddings API, Pinecone, RabbitMQ
- **Key Features:**
  - RabbitMQ consumer for chunk processing
  - Batch embedding generation
  - Vector storage with rich metadata
  - Retry logic and dead letter queue

### 5. RAG Query Service
- **Port:** 8004
- **Responsibility:** Question answering with RAG pipeline
- **Tech:** FastAPI, OpenAI GPT-4, Pinecone, Redis, Langfuse
- **Key Features:**
  - Streaming responses
  - Semantic search (top-k=5)
  - Response caching (Redis)
  - Prompt injection prevention
  - Educational tone enforcement

### 6. Analytics Service
- **Port:** 8005
- **Responsibility:** Student engagement metrics, content analytics
- **Tech:** FastAPI, MongoDB Aggregations, Redis
- **Key Features:**
  - MongoDB aggregation pipelines
  - Student engagement tracking
  - Content popularity metrics
  - Cost and token usage analytics

## Infrastructure Components

### MongoDB
- **Purpose:** Primary database for users, content, questions, analytics
- **Collections:** 
  - users
  - content
  - questions
  - analytics_cache
- **Indexing:** Strategic indexes for performance
- **Connection Pool:** Min 10, Max 100 connections

### Pinecone
- **Purpose:** Vector database for semantic search
- **Configuration:**
  - Dimension: 3072 (OpenAI text-embedding-3-large)
  - Metric: Cosine similarity
  - Namespace per content for isolation
- **Usage:** Store document chunk embeddings with metadata

### Redis
- **Purpose:** Caching and rate limiting
- **Use Cases:**
  - Rate limiting (sorted sets)
  - Response caching (strings with TTL)
  - Session storage
  - Analytics cache
- **Configuration:** 512MB max memory with LRU eviction

### RabbitMQ
- **Purpose:** Message queue for async processing
- **Queues:**
  - chunks.processing (main queue)
  - chunks.failed (dead letter queue)
- **Configuration:** Durable queues, persistent messages, prefetch=10

### Langfuse
- **Purpose:** LLM observability and tracing
- **Integration Points:**
  - Document processing pipeline
  - Embedding generation
  - RAG query pipeline (primary)
  - Token usage tracking
  - Cost tracking per user

## Communication Patterns

### Synchronous (REST APIs)
- User queries -> API Gateway -> RAG Query Service
- Analytics requests -> API Gateway -> Analytics Service
- Auth requests -> API Gateway -> Auth Service

### Asynchronous (Message Queue)
- Document upload -> Document Processor -> RabbitMQ -> Vectorization Service
- Allows handling large documents without blocking
- Retry mechanism for failed processing

## Data Flow

### Document Upload Flow
```
1. User uploads PDF -> API Gateway (auth check)
2. API Gateway -> Document Processing Service
3. Document Processor: Parse with Docling -> Create chunks
4. Store metadata in MongoDB (status: processing)
5. Publish chunks to RabbitMQ queue
6. Vectorization Service consumes from queue
7. Generate embeddings (OpenAI API)
8. Store vectors in Pinecone
9. Update MongoDB (status: completed)
```

### Question Answering Flow
```
1. User asks question -> API Gateway (auth + rate limit)
2. API Gateway -> RAG Query Service
3. Check Redis cache (similar questions)
4. If not cached:
   a. Generate query embedding (OpenAI)
   b. Semantic search in Pinecone (retrieve top-5 chunks)
   c. Construct educational prompt with context
   d. Stream response from GPT-4
   e. Store Q&A in MongoDB
   f. Cache in Redis (TTL: 1 hour)
5. Return streaming response to user
6. Log trace in Langfuse
```

## Security Architecture

### Authentication & Authorization
- JWT-based authentication
- Token expiration: Access (1 hour), Refresh (7 days)
- Role-based access control (RBAC)
- Password hashing: bcrypt with 12 rounds

### Rate Limiting
- Per-user: 100 requests/hour
- Global: 1000 requests/hour
- Redis-based sliding window

### Prompt Injection Prevention
- Input sanitization (remove special chars, length limits)
- System prompt isolation
- Context-aware filtering
- Output validation
- Never allow user input in system prompts

### Data Security
- Environment variables for secrets
- No hardcoded credentials
- HTTPS in production
- Input validation with Pydantic models
- File upload size limits (50MB)

## Scalability Strategy

### Horizontal Scaling
- Each service can scale independently
- Stateless services (except Redis cache)
- Load balancing at API Gateway level

### Database Optimization
- Connection pooling
- Strategic indexing
- Aggregation pipeline optimization
- Query result caching

### Caching Strategy
- L1: In-memory (per service)
- L2: Redis (shared cache)
- Cache invalidation: TTL-based

### Async Processing
- Document processing offloaded to queue
- Non-blocking operations
- Batch processing for embeddings

## Observability & Monitoring

### Langfuse Integration
- Trace every LLM interaction
- Track costs per user/content
- Monitor response times
- Identify bottlenecks

### Logging
- Structured JSON logging
- Centralized logs (Docker logging driver)
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Include: service_name, trace_id, timestamp

### Health Checks
- Each service: `/health` endpoint
- API Gateway aggregates health status
- Dependency checks (DB, Redis, Queue)

### Metrics
- Response time (p50, p95, p99)
- Error rates
- Cache hit rates
- Queue depth
- Token usage
- API costs

## Error Handling

### Strategy
- Custom exception hierarchy
- Global exception handlers in FastAPI
- Retry logic with exponential backoff
- Circuit breaker for external APIs
- Graceful degradation

### Error Types
- ValidationError: Input validation failures
- AuthenticationError: Auth failures
- RateLimitError: Rate limit exceeded
- ExternalServiceError: OpenAI, Pinecone errors
- DocumentProcessingError: Parsing failures

## Development & Deployment

### Development Environment
- Docker Compose for all services
- Hot reloading enabled
- Development .env file
- Local ports exposed

### Production Deployment (AWS EC2)
- Docker Compose on EC2 instance
- Nginx reverse proxy with SSL
- Environment-specific configurations
- Security groups (only 80, 443 open)
- Automated health checks

### CI/CD (Bonus)
- GitHub Actions
- Automated testing
- Docker image building
- Deployment to EC2

## Technology Stack Summary

| Component | Technology |
|-----------|-----------|
| API Framework | FastAPI |
| Language | Python 3.11+ |
| Document Parsing | Docling |
| LLM | OpenAI GPT-4 |
| Embeddings | OpenAI text-embedding-3-large |
| Vector DB | Pinecone |
| Database | MongoDB |
| Cache | Redis |
| Message Queue | RabbitMQ |
| Authentication | JWT (PyJWT) |
| Password Hashing | bcrypt |
| Observability | Langfuse |
| Containerization | Docker & Docker Compose |
| Deployment | AWS EC2 |

## Performance Targets

- **Document Processing:** < 30 seconds for 100-page PDF
- **Query Response Time:** < 3 seconds (including streaming start)
- **Cache Hit Rate:** > 90% for common questions
- **System Uptime:** 99.9%
- **Concurrent Users:** Support 100+ concurrent users

## Cost Optimization

- Response caching reduces OpenAI API calls
- Batch embedding generation
- Connection pooling reduces overhead
- Efficient MongoDB queries with indexing
- Rate limiting prevents abuse

## Next Steps

1. Review each service's detailed plan
2. Set up project structure
3. Configure Docker Compose
4. Implement shared components
5. Build services incrementally
6. Write tests
7. Deploy to AWS EC2

