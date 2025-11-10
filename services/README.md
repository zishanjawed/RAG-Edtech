# RAG Edtech Backend Services

Microservices backend for the RAG Edtech platform built with Python and FastAPI.

## Architecture Overview

6 independent microservices:

```
API Gateway (8000)
    ├── Auth Service (8001)
    ├── Document Processor (8002)
    ├── Vectorization Service (8003)
    ├── RAG Query Service (8004)
    └── Analytics Service (8005)
```

## Services

### 1. API Gateway (Port 8000)
- Entry point for all requests
- JWT authentication middleware
- Rate limiting (Redis)
- Request routing
- CORS configuration

**Location:** `services/api-gateway/`

### 2. Auth Service (Port 8001)
- User registration
- JWT-based login
- Token refresh
- Password hashing (bcrypt)
- Role-based access control

**Location:** `services/auth/`

### 3. Document Processor (Port 8002)
- Document upload (PDF, MD, TXT, DOCX)
- Text extraction and parsing
- Hierarchical chunking
- RabbitMQ publisher

**Location:** `services/document-processor/`

### 4. Vectorization Service (Port 8003)
- RabbitMQ consumer
- Embedding generation (OpenAI)
- Pinecone vector storage
- Batch processing

**Location:** `services/vectorization/`

### 5. RAG Query Service (Port 8004)
- Question answering
- Semantic search (Pinecone)
- GPT-4 streaming responses
- Redis caching
- Prompt injection prevention

**Location:** `services/rag-query/`

### 6. Analytics Service (Port 8005)
- Student engagement metrics
- Content usage analytics
- MongoDB aggregations
- Teacher dashboard data

**Location:** `services/analytics/`

## Quick Start

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- OpenAI API key
- Pinecone API key

### Installation

1. **Set up environment**
```bash
cd RAG-Edtech
cp .env.example .env
# Edit .env with your API keys
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Start infrastructure**
```bash
docker-compose up -d mongodb redis rabbitmq
```

4. **Start all services**
```bash
docker-compose up -d
```

Or run individual services:
```bash
cd services/auth
uvicorn main:app --reload --port 8001
```

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | FastAPI | High-performance async API |
| Language | Python 3.11 | Backend language |
| Database | MongoDB 7.0 | Document storage |
| Cache | Redis 7.2 | Caching, rate limiting |
| Queue | RabbitMQ 3.12 | Async processing |
| Vector DB | Pinecone | Semantic search |
| LLM | OpenAI GPT-4 | Answer generation |
| Embeddings | text-embedding-3-large | Vector embeddings |
| Observability | Langfuse | LLM tracing |

## Environment Variables

Required variables in `.env`:

```env
# OpenAI
OPENAI_API_KEY=sk-your-key-here

# Pinecone
PINECONE_API_KEY=your-key-here
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=edtech-rag-index

# JWT
JWT_SECRET=your-secure-secret-min-32-characters

# MongoDB
MONGO_USERNAME=admin
MONGO_PASSWORD=password123
MONGO_DATABASE=rag_edtech

# RabbitMQ
RABBITMQ_USER=admin
RABBITMQ_PASSWORD=password123

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Langfuse (Optional)
LANGFUSE_PUBLIC_KEY=pk-your-key
LANGFUSE_SECRET_KEY=sk-your-secret
```

## Testing

### Run All Tests
```bash
pytest
```

### Run Specific Service Tests
```bash
pytest services/auth/tests/ -v
pytest services/rag-query/tests/ -v
```

### Run with Coverage
```bash
pytest --cov=services --cov=shared --cov-report=html
open htmlcov/index.html
```

## Service Structure

Each service follows this structure:

```
service-name/
├── main.py              # FastAPI application
├── config.py            # Configuration
├── models/              # Pydantic models
├── tests/               # Unit tests
├── Dockerfile           # Container definition
└── requirements.txt     # Dependencies
```

## Shared Module

The `shared/` directory contains utilities used across all services:

```
shared/
├── config/              # Configuration management
├── database/            # MongoDB and Redis clients
├── exceptions/          # Custom exceptions
├── logging/             # Structured logging
├── middleware/          # FastAPI middleware
├── observability/       # Langfuse integration
└── utils/               # Utilities (retry, security)
```

## Development Workflow

### Run Individual Service

```bash
cd services/auth
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### Add New Endpoint

1. Add route to service's `main.py`
2. Create Pydantic models
3. Implement business logic
4. Add unit tests
5. Update documentation

### Debug

```python
# Add logging
import logging
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.error("Error", exc_info=True)
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f rag-query

# Last 100 lines
docker-compose logs --tail=100 api-gateway
```

## API Documentation

Each service exposes interactive API docs:

- API Gateway: http://localhost:8000/docs
- Auth Service: http://localhost:8001/docs
- Document Processor: http://localhost:8002/docs
- Vectorization: http://localhost:8003/docs
- RAG Query: http://localhost:8004/docs
- Analytics: http://localhost:8005/docs

## Common Tasks

### Check Service Health

```bash
curl http://localhost:8000/health
```

### Test Authentication

```bash
# Register
curl -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","full_name":"Test","role":"student"}'

# Login
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'
```

### Check MongoDB

```bash
docker exec -it rag-edtech-mongodb-1 mongosh -u admin -p password123
> use rag_edtech
> db.users.find()
```

### Check Redis

```bash
docker exec -it rag-edtech-redis-1 redis-cli
> PING
> KEYS *
```

### Check RabbitMQ

Visit: http://localhost:15672
Login: admin / password123

## Troubleshooting

### Service Won't Start

```bash
# Check if port is in use
lsof -i :8000

# Kill process
kill -9 <PID>

# Restart service
docker-compose restart api-gateway
```

### MongoDB Connection Failed

```bash
# Check MongoDB is running
docker-compose ps mongodb

# Restart MongoDB
docker-compose restart mongodb

# Check connection
docker exec -it rag-edtech-mongodb-1 mongosh -u admin -p password123
```

### RabbitMQ Queue Issues

```bash
# Check queue status
# Visit: http://localhost:15672

# Purge queue (dev only)
# Use RabbitMQ management UI

# Restart consumer
docker-compose restart vectorization
```

### Pinecone Connection Failed

1. Verify API key: `echo $PINECONE_API_KEY`
2. Check index exists in Pinecone dashboard
3. Verify index dimensions match (3072)

## Deployment

### Production Checklist

- [ ] Set strong JWT_SECRET (min 32 chars)
- [ ] Use production MongoDB instance
- [ ] Configure Redis with persistence
- [ ] Set up RabbitMQ cluster
- [ ] Enable HTTPS with SSL certificates
- [ ] Configure rate limits
- [ ] Set up monitoring
- [ ] Enable log aggregation
- [ ] Configure backups

### Docker Production Build

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Documentation

For complete documentation including architecture, API reference, RAG pipeline details, and troubleshooting, see [PROJECT_MASTER.md](../PROJECT_MASTER.md).

## License

MIT

