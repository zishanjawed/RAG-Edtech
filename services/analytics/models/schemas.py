"""
Pydantic models for analytics service.
"""
from pydantic import BaseModel
from typing import List, Dict, Any


class StudentEngagement(BaseModel):
    """Student engagement metrics."""
    student_id: str
    total_questions: int
    unique_content_accessed: int
    avg_response_time_ms: int
    first_activity: str | None = None
    last_activity: str
    recent_questions: List[Dict[str, Any]] = []
    # Legacy fields for backward compatibility
    recent_questions_7d: int = 0
    total_tokens_used: int = 0
    top_content: List[Dict[str, Any]] = []
    daily_activity: List[Dict[str, Any]] = []


class ContentStats(BaseModel):
    """Content statistics."""
    content_id: str
    total_questions: int
    unique_students: int
    avg_response_time_ms: int
    cache_hit_rate: float
    question_samples: List[str]

