# RAG Edtech Platform 🎓

**Production-ready AI-powered educational platform with advanced RAG capabilities**

> A comprehensive document management and AI tutoring system featuring real-time processing, global chat across documents, and LLM-generated study questions.

---

## ✨ New Features (November 2025)

- 📚 **Documents Hub** - Centralized management with advanced filtering
- 🌐 **Global Chat** - Search across multiple documents simultaneously
- 💡 **AI-Generated Questions** - Context-aware suggested questions per document
- ⚡ **Real-Time Updates** - WebSocket status for document processing
- 🏷️ **Smart Tagging** - Organize documents with custom tags
- 🔍 **Advanced Search** - Filter by subject, tags, ownership
- 🎯 **@-Mentions** - Narrow global search to specific documents
- 👨‍🏫 **Teacher Access** - View all student documents and activity

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- OpenAI API key
- Pinecone API key

### Setup

```bash
# 1. Clone and configure
git clone <repository-url>
cd RAG-Edtech
cp .env.example .env
# Edit .env with your API keys

# 2. Install dependencies
pip install websockets date-fns

# 3. Start backend services
docker-compose up -d
sleep 30  # Wait for services to initialize

# 4. Create users and seed data
python scripts/create_users.py
python scripts/seed_sample_data.py

# 5. Start frontend
cd frontend
npm install
npm run dev
```

### Access

- **Frontend:** http://localhost:3000
- **API Gateway:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### Login

**Student:** `tony.stark@avengers.com` / `TestPass@123`  
**Teacher:** `steve.rogers@avengers.com` / `TestPass@123`

> **See [RUN_ME_FIRST.md](RUN_ME_FIRST.md) for detailed testing guide**

---

## Basic Usage

### 1. Register User
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe",
    "role": "student"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "student@example.com", "password": "SecurePass123!"}'
```

### 3. Upload Document
```bash
curl -X POST http://localhost:8000/api/content/upload \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@document.pdf" \
  -F "user_id=<user_id>"
```

### 4. Ask Question
```bash
curl -X POST http://localhost:8000/api/content/<content_id>/question \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is a covalent bond?", "user_id": "<user_id>"}'
```

## Architecture

6 microservices + Modern React frontend:
- **API Gateway** (8000): Entry point, rate limiting
- **Auth Service** (8001): JWT authentication
- **Document Processor** (8002): PDF/MD/TXT parsing
- **Vectorization** (8003): Embedding generation
- **RAG Query** (8004): Question answering with GPT-4
- **Analytics** (8005): Student engagement metrics
- **Frontend** (3000): React + TypeScript UI

## 📚 Documentation

### Getting Started
- 🏁 **[RUN_ME_FIRST.md](RUN_ME_FIRST.md)** - Quick start guide (5 minutes)
- 📋 **[SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md)** - Complete setup steps
- ✅ **[TEST_CHECKLIST.md](TEST_CHECKLIST.md)** - Testing guide

### Architecture & Implementation
- 📖 **[PROJECT_MASTER.md](PROJECT_MASTER.md)** - Complete documentation (single source of truth)
- 🏗️ **[BACKEND_IMPLEMENTATION_NOTES.md](BACKEND_IMPLEMENTATION_NOTES.md)** - API specifications
- 🎨 **[FRONTEND_IMPLEMENTATION_SUMMARY.md](FRONTEND_IMPLEMENTATION_SUMMARY.md)** - Frontend architecture

### Guides
- 🧪 **[QUICK_START_GUIDE.md](QUICK_START_GUIDE.md)** - Feature testing walkthrough
- 🎯 **[SESSION_3_COMPLETION_SUMMARY.md](SESSION_3_COMPLETION_SUMMARY.md)** - Latest implementation details

## 🎯 Key Features

### Document Management
- 📤 Upload materials (PDF, MD, TXT, DOCX) with tags
- 🔄 Real-time processing status via WebSocket
- 🔍 Advanced filtering (All/Owned/Shared)
- 🔎 Instant search across title, subject, tags
- 🏷️ Custom tagging for organization
- ♻️ Automatic duplicate detection (75% cost savings)

### AI-Powered Chat
- 💬 Document-specific chat with streaming
- 🌐 Global chat across entire knowledge base
- 🎯 @-Mention system to narrow search
- 💡 LLM-generated suggested questions (GPT-4o-mini)
- 📊 Source citations with similarity scores
- ⚡ Fast mode or complete mode with sources

### Analytics & Dashboards
- 👨‍🎓 Student engagement metrics
- 👨‍🏫 Teacher dashboard (all students)
- 📈 Content usage analytics
- 🎨 Modern React UI with animations

### Security & Performance
- 🔐 Secure JWT authentication
- 🚦 Rate limiting with Redis
- 💾 Response caching (90%+ hit rate)
- 🔒 Prompt injection prevention
- 📊 LLM observability with Langfuse
- 🎭 Role-based access control

## Tech Stack

**Backend:** Python, FastAPI, MongoDB, Pinecone, Redis, RabbitMQ  
**Frontend:** React 18, TypeScript, TailwindCSS, Zustand, React Query  
**AI:** OpenAI GPT-4, text-embedding-3-large  
**Infrastructure:** Docker, Nginx, Let's Encrypt

## Testing

```bash
# Backend tests
pytest

# Frontend tests
cd frontend
npm run type-check
npm run lint
```

## Support

For detailed information, troubleshooting, and development workflows, see [PROJECT_MASTER.md](PROJECT_MASTER.md).

## License

MIT
