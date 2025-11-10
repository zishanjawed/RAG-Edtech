# Backend Implementation Notes for Documents Hub & Global Chat

**Created:** November 10, 2025  
**Status:** Frontend Complete (Mock Data) - Backend Implementation Pending

---

## Overview

This document outlines the backend implementation requirements for the new Documents Hub and Global Chat features. The frontend has been fully implemented using mock data and simulated APIs. This guide will help implement the real backend endpoints.

---

## 1. Documents Management API

### 1.1 Get User Documents with Filters

**Endpoint:** `GET /api/content/user/{user_id}`

**Query Parameters:**
- `filter`: `all` | `owned` | `shared` (default: `all`)
- `search`: string (optional) - searches title, subject, tags
- `subjects`: comma-separated list (optional) - filter by subjects
- `tags`: comma-separated list (optional) - filter by tags
- `page`: integer (optional, default: 1)
- `limit`: integer (optional, default: 50)

**Response:**
```json
{
  "documents": [
    {
      "content_id": "uuid",
      "title": "Document Title",
      "file_path": "/uploads/...",
      "file_type": "pdf",
      "file_size": 2457600,
      "user_id": "uuid",
      "instructor_id": "uuid",
      "grade_level": "IB Diploma",
      "subject": "Chemistry",
      "status": "completed",
      "chunks_count": 45,
      "upload_date": "2025-11-05T10:30:00Z",
      "processed_date": "2025-11-05T10:35:00Z",
      "content_hash": "sha256-hash",
      "is_duplicate": false,
      "original_uploader_id": "uuid",
      "original_upload_date": "2025-11-05T10:30:00Z",
      "upload_history": [...],
      "tags": ["stoichiometry", "moles"],
      "last_activity": "2025-11-09T14:20:00Z",
      "uploader_name": "Tony Stark",
      "is_owned": true,
      "is_shared": false
    }
  ],
  "total": 6,
  "page": 1,
  "pages": 1
}
```

**Implementation Notes:**
- `is_owned`: True if `user_id` matches current user OR user is in `upload_history`
- `is_shared`: True if document is in user's shared documents (future: explicit sharing feature)
- `last_activity`: Most recent question timestamp for this document
- `uploader_name`: Lookup from users collection using `original_uploader_id`

### 1.2 Document Mention Typeahead

**Endpoint:** `GET /api/content/mentions`

**Query Parameters:**
- `q`: string - search query
- `user_id`: string - current user
- `limit`: integer (default: 5)

**Response:**
```json
{
  "documents": [
    {
      "content_id": "uuid",
      "title": "Document Title",
      "subject": "Chemistry",
      "tags": ["tag1", "tag2"]
    }
  ]
}
```

**Implementation Notes:**
- Only return documents accessible to the user (owned or shared)
- Search in title, subject, and tags
- Return minimal fields for performance
- Used for @-mention autocomplete in global chat

---

## 2. Global Chat API

### 2.1 Global Question (Streaming)

**Endpoint:** `POST /api/query/global/question`

**Request:**
```json
{
  "question": "What is stoichiometry?",
  "user_id": "uuid",
  "selected_doc_ids": ["uuid1", "uuid2"]  // Optional - from @mentions
}
```

**Response:** Server-Sent Events (SSE) stream
```
data: {"type": "token", "content": "Stoichiometry"}
data: {"type": "token", "content": " is"}
data: {"type": "token", "content": " the"}
...
data: {"type": "complete"}
```

**Implementation Notes:**
- If `selected_doc_ids` is empty, search across ALL documents accessible to user
- If `selected_doc_ids` provided, restrict search to those documents only
- Use Pinecone filter: `{"content_id": {"$in": [accessible_doc_ids]}}`
- Stream response tokens as they're generated
- Store question in MongoDB after completion

### 2.2 Global Question (Complete with Sources)

**Endpoint:** `POST /api/query/global/complete`

**Request:**
```json
{
  "question": "What is stoichiometry?",
  "user_id": "uuid",
  "selected_doc_ids": ["uuid1", "uuid2"]  // Optional
}
```

**Response:**
```json
{
  "question_id": "uuid",
  "question": "What is stoichiometry?",
  "answer": "Stoichiometry is...",
  "sources": [
    {
      "source_id": 1,
      "document_title": "IB Chemistry: Stoichiometry",
      "uploader_name": "Tony Stark",
      "uploader_id": "uuid",
      "upload_date": "2025-11-05",
      "chunk_index": 12,
      "similarity_score": 0.94
    }
  ],
  "metadata": {
    "chunks_used": 8,
    "documents_searched": 6,
    "response_time_ms": 3250,
    "llm_time_ms": 2800,
    "tokens_used": {
      "prompt_tokens": 2100,
      "completion_tokens": 420,
      "total_tokens": 2520
    },
    "model": "gpt-4-0613"
  },
  "cached": false
}
```

**Implementation Notes:**
- Similar to document-specific complete endpoint
- Search across multiple documents
- Return sources from different documents
- Include `documents_searched` count in metadata
- Cache key should include sorted `selected_doc_ids` if provided

---

## 3. Suggested Prompts API

### 3.1 Get Document-Specific Prompts

**Endpoint:** `GET /api/prompts/suggest`

**Query Parameters:**
- `scope`: `document` | `global`
- `content_id`: string (required if scope=document)
- `user_id`: string

**Response:**
```json
{
  "prompts": [
    {
      "id": "prompt-1",
      "text": "Explain the key concepts in this chapter",
      "category": "explanation",
      "icon": "lightbulb"
    },
    {
      "id": "prompt-2",
      "text": "What are the main definitions I need to know?",
      "category": "definition",
      "icon": "book-open"
    }
  ]
}
```

**Implementation Notes:**

**For Document Scope:**
- Generate prompts based on document metadata (subject, title, tags)
- Templates by subject:
  - Chemistry: "Explain [topic]", "What are common mistakes with [topic]?"
  - Math: "Walk me through solving [type] problems"
  - General: "Summarize the main points", "What should I focus on for the exam?"

**For Global Scope:**
- Analyze user's document collection
- Generate cross-document prompts:
  - "Compare [topic A] across my documents"
  - "What are the connections between [subject 1] and [subject 2]?"
  - "Create a study plan based on my knowledge base"
  - "What topics am I missing in my [subject] notes?"

**Categories:**
- `definition`: "What is...", "Define..."
- `explanation`: "Explain...", "Why..."
- `comparison`: "Compare...", "What's the difference..."
- `procedure`: "How to...", "Steps for..."
- `application`: "Apply...", "Solve..."
- `evaluation`: "Analyze...", "Evaluate..."

---

## 4. Database Schema Updates

### 4.1 Content Collection Updates

Add these fields to existing `content` collection:

```javascript
{
  // ... existing fields ...
  
  // UI helper fields
  tags: [String],              // Array of tags for filtering
  last_activity: DateTime,     // Most recent question timestamp
  
  // Sharing fields (future)
  shared_with: [               // Array of users with access
    {
      user_id: String,
      role: String,            // "viewer" | "editor"
      shared_date: DateTime
    }
  ]
}
```

**Indexes:**
```javascript
content.createIndex({ "shared_with.user_id": 1 })
content.createIndex({ tags: 1 })
content.createIndex({ last_activity: -1 })
```

### 4.2 Questions Collection Updates

Add global question support:

```javascript
{
  // ... existing fields ...
  
  is_global: Boolean,          // True if global search
  searched_doc_ids: [String],  // Documents searched (if narrowed)
  documents_searched: Number   // Total docs searched
}
```

**Indexes:**
```javascript
questions.createIndex({ is_global: 1, created_at: -1 })
questions.createIndex({ searched_doc_ids: 1 })
```

---

## 5. Pinecone Query Updates

### 5.1 Global Search Query

```python
# Get all accessible document IDs for user
accessible_docs = get_user_accessible_docs(user_id)

# If user selected specific docs via @mentions
if selected_doc_ids:
    doc_ids = selected_doc_ids
else:
    doc_ids = accessible_docs

# Query Pinecone with filter
results = index.query(
    vector=query_embedding,
    top_k=10,  # More results for global search
    include_metadata=True,
    filter={
        "content_id": {"$in": doc_ids}
    }
)

# Group results by document for diversity
# Take top 2-3 chunks per document, max 8 total
diverse_results = diversify_results(results, max_per_doc=2, max_total=8)
```

### 5.2 Result Diversification

```python
def diversify_results(results, max_per_doc=2, max_total=8):
    """
    Ensure results come from multiple documents for global search
    """
    by_doc = {}
    for match in results.matches:
        doc_id = match.metadata['content_id']
        if doc_id not in by_doc:
            by_doc[doc_id] = []
        by_doc[doc_id].append(match)
    
    # Round-robin selection
    diverse = []
    while len(diverse) < max_total and any(by_doc.values()):
        for doc_id, matches in by_doc.items():
            if matches and len([m for m in diverse if m.metadata['content_id'] == doc_id]) < max_per_doc:
                diverse.append(matches.pop(0))
                if len(diverse) >= max_total:
                    break
    
    return diverse
```

---

## 6. Caching Strategy

### 6.1 Global Chat Cache Keys

```python
def generate_global_cache_key(question: str, doc_ids: List[str]) -> str:
    """
    Generate cache key for global questions
    """
    # Sort doc_ids for consistent cache hits
    sorted_ids = sorted(doc_ids) if doc_ids else ["all"]
    key_parts = [question.lower().strip()] + sorted_ids
    combined = ":".join(key_parts)
    hash_obj = hashlib.md5(combined.encode())
    return f"rag:global:{hash_obj.hexdigest()}"
```

### 6.2 Cache Invalidation

- Document upload: Clear global cache (or use doc-specific keys)
- Document update: Clear related caches
- TTL: 1 hour for global queries (configurable)

---

## 7. Access Control

### 7.1 Document Access Rules

```python
def get_user_accessible_docs(user_id: str, role: str) -> List[str]:
    """
    Get all document IDs accessible to user
    """
    # Documents owned by user
    owned = db.content.find(
        {"user_id": user_id},
        {"content_id": 1}
    )
    
    # Documents in upload_history (deduplication)
    in_history = db.content.find(
        {"upload_history.user_id": user_id},
        {"content_id": 1}
    )
    
    # Documents explicitly shared (future feature)
    shared = db.content.find(
        {"shared_with.user_id": user_id},
        {"content_id": 1}
    )
    
    # Teachers can access all documents (optional policy)
    if role == "teacher":
        all_docs = db.content.find(
            {"status": "completed"},
            {"content_id": 1}
        )
        return [doc["content_id"] for doc in all_docs]
    
    # Combine and deduplicate
    all_accessible = set()
    for doc in owned:
        all_accessible.add(doc["content_id"])
    for doc in in_history:
        all_accessible.add(doc["content_id"])
    for doc in shared:
        all_accessible.add(doc["content_id"])
    
    return list(all_accessible)
```

---

## 8. Performance Considerations

### 8.1 Optimization Tips

1. **Document List Pagination:**
   - Implement cursor-based pagination for large collections
   - Cache document counts per filter

2. **Global Search Performance:**
   - Limit to 10-15 documents max per query
   - Use Pinecone metadata filtering (server-side)
   - Implement query timeout (30s max)

3. **Suggested Prompts:**
   - Cache prompts per document (TTL: 24 hours)
   - Generate global prompts on-demand, cache for user

4. **Typeahead Search:**
   - Use MongoDB text index on title, subject, tags
   - Limit results to 5-10 items
   - Debounce on frontend (already implemented)

### 8.2 Rate Limiting

Add specific limits for global chat:
- Global questions: 20/hour per user (more expensive than single-doc)
- Document list: 100/hour per user
- Typeahead: 50/minute per user

---

## 9. Error Handling

### 9.1 Common Error Scenarios

1. **No Accessible Documents:**
```json
{
  "error": "no_documents",
  "message": "You don't have any documents to search. Please upload a document first.",
  "code": 404
}
```

2. **Selected Documents Not Accessible:**
```json
{
  "error": "access_denied",
  "message": "Some selected documents are not accessible to you.",
  "accessible_ids": ["uuid1"],
  "inaccessible_ids": ["uuid2"],
  "code": 403
}
```

3. **Query Too Broad:**
```json
{
  "error": "query_too_broad",
  "message": "Searching across 50+ documents. Please narrow your search using @mentions.",
  "document_count": 52,
  "code": 400
}
```

---

## 10. Testing Checklist

### 10.1 Documents API Tests

- [ ] Get all documents (no filters)
- [ ] Filter by owned documents
- [ ] Filter by shared documents
- [ ] Search by title
- [ ] Search by subject
- [ ] Search by tags
- [ ] Pagination works correctly
- [ ] Empty results handled
- [ ] Access control enforced

### 10.2 Global Chat Tests

- [ ] Query across all documents
- [ ] Query with @mentioned documents
- [ ] Query with no accessible documents (error)
- [ ] Query with inaccessible @mentions (error)
- [ ] Streaming response works
- [ ] Complete response includes sources
- [ ] Sources from multiple documents
- [ ] Cache hit/miss scenarios
- [ ] Rate limiting enforced

### 10.3 Suggested Prompts Tests

- [ ] Document-specific prompts generated
- [ ] Global prompts generated
- [ ] Prompts vary by subject
- [ ] Prompts cached correctly
- [ ] Empty document collection handled

---

## 11. Migration Plan

### 11.1 Phase 1: Basic Implementation (Week 1)

1. Implement document list endpoint with filters
2. Update existing complete endpoint to support global queries
3. Add basic suggested prompts (static templates)

### 11.2 Phase 2: Advanced Features (Week 2)

1. Implement streaming for global chat
2. Add typeahead search endpoint
3. Implement result diversification
4. Add caching for global queries

### 11.3 Phase 3: Optimization (Week 3)

1. Optimize Pinecone queries
2. Implement advanced caching strategies
3. Add comprehensive error handling
4. Performance testing and tuning

---

## 12. Frontend Integration Notes

### 12.1 Environment Variables

Add to `.env`:
```env
VITE_USE_MOCKS=false  # Set to false when backend is ready
```

### 12.2 Service Layer Updates

When backend is ready, update these files:
- `frontend/src/api/documents.service.ts` - Replace mock calls
- `frontend/src/api/chat.service.ts` - Add global chat methods
- `frontend/src/features/documents/mock/documents.mock.ts` - Can be removed
- `frontend/src/features/chat/mock/chat.mock.ts` - Can be removed

### 12.3 Type Safety

All TypeScript types are already defined in:
- `frontend/src/api/types.ts`

No changes needed to types when switching from mock to real API.

---

## 13. Security Considerations

### 13.1 Input Validation

- Sanitize all search queries
- Validate document IDs exist and are accessible
- Limit query length (500 chars max)
- Prevent SQL/NoSQL injection in filters

### 13.2 Access Control

- Always verify user has access to documents before querying
- Log all global searches for audit
- Implement rate limiting per user
- Monitor for abuse patterns

### 13.3 Data Privacy

- Don't leak document content in error messages
- Sanitize source citations (remove sensitive metadata)
- Implement proper CORS for production
- Use HTTPS only in production

---

## 14. Monitoring & Observability

### 14.1 Metrics to Track

- Global query response times
- Documents searched per query (avg/max)
- Cache hit rates for global queries
- Error rates by type
- User engagement with suggested prompts
- @mention usage frequency

### 14.2 Langfuse Integration

Add these tags to global query traces:
```python
trace = langfuse.trace(
    name="global_rag_query",
    user_id=user_id,
    metadata={
        "is_global": True,
        "documents_searched": len(doc_ids),
        "selected_docs": len(selected_doc_ids) if selected_doc_ids else 0,
        "has_mentions": bool(selected_doc_ids)
    }
)
```

---

## 15. Future Enhancements

### 15.1 Explicit Document Sharing

- Add sharing UI in frontend
- Implement share permissions (viewer/editor)
- Share via email/link
- Track share analytics

### 15.2 Smart Prompt Generation

- Use LLM to generate personalized prompts
- Analyze user's question history
- Suggest follow-up questions
- Multi-turn conversation support

### 15.3 Advanced Search

- Semantic search across documents
- Filter by date range
- Filter by uploader
- Save search queries
- Search history

---

## Contact & Support

For questions about implementation:
- Review this document first
- Check PROJECT_MASTER.md for overall architecture
- Refer to existing single-document endpoints as examples
- Test with mock data first before backend integration

**Implementation Priority:** High  
**Estimated Backend Effort:** 2-3 weeks  
**Dependencies:** Existing RAG pipeline, Pinecone, MongoDB

---

*End of Backend Implementation Notes*

