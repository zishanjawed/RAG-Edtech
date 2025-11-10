"""
Pydantic models for RAG query service.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class QuestionRequest(BaseModel):
    """Request model for asking a question."""
    question: str = Field(..., min_length=1, max_length=500, description="The question to ask")
    user_id: str = Field(..., description="User ID asking the question")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is a covalent bond?",
                "user_id": "user123"
            }
        }


class GlobalChatRequest(BaseModel):
    """Request model for global chat across documents."""
    question: str = Field(..., min_length=1, max_length=500, description="The question to ask")
    user_id: str = Field(..., description="User ID asking the question")
    # Accept both snake_case and camelCase payloads
    selected_doc_ids: Optional[List[str]] = Field(
        default=None,
        alias="selectedDocIds",
        description="Optional list of document IDs to narrow search"
    )
    
    class Config:
        allow_population_by_field_name = True
        json_schema_extra = {
            "example": {
                "question": "Compare stoichiometry concepts across my documents",
                "user_id": "user123",
                "selectedDocIds": ["doc1", "doc2"]
            }
        }


class SourceReference(BaseModel):
    """Source reference for citations in responses."""
    source_id: int  # Source number (1, 2, 3, etc.)
    document_title: str
    uploader_name: str
    uploader_id: str
    upload_date: str
    chunk_index: int
    similarity_score: float


class QuestionResponse(BaseModel):
    """Response model for question answering with source attribution."""
    question_id: Optional[str] = None
    content_id: str
    question: str
    answer: str
    sources: List[SourceReference] = []  # Source citations
    metadata: Dict[str, Any] = {}
    cached: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "question_id": "q123",
                "content_id": "c456",
                "question": "What is a covalent bond?",
                "answer": "A covalent bond is a chemical bond...",
                "sources": [
                    {
                        "source_id": 1,
                        "document_title": "IB Chemistry Notes",
                        "uploader_name": "Tony Stark",
                        "uploader_id": "user123",
                        "upload_date": "2025-11-10",
                        "chunk_index": 5,
                        "similarity_score": 0.92
                    }
                ],
                "metadata": {
                    "chunks_used": 3,
                    "response_time_ms": 1500,
                    "tokens_used": {"prompt": 100, "completion": 50, "total": 150}
                },
                "cached": False
            }
        }


class GlobalChatResponse(BaseModel):
    """Response model for global chat across documents."""
    question_id: str
    question: str
    answer: str
    sources: List[SourceReference] = []
    metadata: Dict[str, Any] = {}
    cached: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "question_id": "q789",
                "question": "Compare thermodynamics across my chemistry notes",
                "answer": "Based on your documents...",
                "sources": [...],
                "metadata": {
                    "chunks_used": 8,
                    "documents_searched": 4,
                    "response_time_ms": 3200
                },
                "cached": False
            }
        }

