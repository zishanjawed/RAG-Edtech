"""
Pydantic models for document processing service.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4


class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    content_id: str
    filename: str
    file_type: str
    status: str
    total_chunks: int
    message: str
    is_duplicate: bool = False  # Indicates if document was a duplicate
    duplicate_of: Optional[str] = None  # Original content_id if duplicate


class UploadHistoryEntry(BaseModel):
    """Single entry in document upload history."""
    user_id: str
    user_name: str
    upload_date: datetime
    filename: str
    content_hash: str


class ContentMetadata(BaseModel):
    """Content metadata stored in MongoDB with deduplication and traceability."""
    content_id: str = Field(default_factory=lambda: str(uuid4()))
    filename: str
    file_type: str
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    user_id: str  # Current owner/uploader
    
    # Deduplication fields
    content_hash: Optional[str] = None  # SHA-256 hash of content
    is_duplicate: bool = False  # Flag if this is a duplicate upload
    
    # Traceability fields
    original_uploader_id: str = None  # First person who uploaded this content
    original_upload_date: datetime = Field(default_factory=datetime.utcnow)
    upload_history: List[Dict[str, Any]] = []  # Track all uploaders
    
    # Version tracking (for future content updates)
    version_number: int = 1
    parent_content_id: Optional[str] = None  # For version lineage
    
    # Processing status
    status: str = "processing"  # processing, completed, failed
    total_chunks: int = 0
    processed_chunks: int = 0
    
    # Tags for filtering and organization
    tags: List[str] = []
    
    # Additional metadata
    metadata: Dict[str, Any] = {}
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DocumentChunk(BaseModel):
    """Model for a document chunk."""
    content_id: str
    chunk_index: int
    text: str
    token_count: int
    metadata: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "content_id": "123e4567-e89b-12d3-a456-426614174000",
                "chunk_index": 0,
                "text": "This is a sample chunk of text...",
                "token_count": 100,
                "metadata": {
                    "section_title": "Introduction",
                    "page_number": 1
                }
            }
        }

