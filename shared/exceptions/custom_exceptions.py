"""
Custom exception hierarchy for the RAG Edtech platform.
Provides structured error handling across all services.
"""
from typing import Any, Dict, Optional


class RAGEdtechException(Exception):
    """Base exception for all RAG Edtech errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details
        }


# Authentication & Authorization Exceptions
class AuthenticationError(RAGEdtechException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, details=details)


class AuthorizationError(RAGEdtechException):
    """Raised when user lacks permission for an action."""
    
    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=403, details=details)


class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is invalid or expired."""
    
    def __init__(self, message: str = "Invalid or expired token", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details=details)


# Validation Exceptions
class ValidationError(RAGEdtechException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, details=details)


class FileValidationError(ValidationError):
    """Raised when file validation fails."""
    
    def __init__(self, message: str = "Invalid file", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details=details)


# Rate Limiting Exceptions
class RateLimitError(RAGEdtechException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=429, details=details)


# External Service Exceptions
class ExternalServiceError(RAGEdtechException):
    """Raised when external service call fails."""
    
    def __init__(self, service: str, message: str = "External service error", details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details['service'] = service
        super().__init__(message, status_code=503, details=details)


class OpenAIError(ExternalServiceError):
    """Raised when OpenAI API call fails."""
    
    def __init__(self, message: str = "OpenAI API error", details: Optional[Dict[str, Any]] = None):
        super().__init__("OpenAI", message, details)


class PineconeError(ExternalServiceError):
    """Raised when Pinecone API call fails."""
    
    def __init__(self, message: str = "Pinecone API error", details: Optional[Dict[str, Any]] = None):
        super().__init__("Pinecone", message, details)


# Document Processing Exceptions
class DocumentProcessingError(RAGEdtechException):
    """Raised when document processing fails."""
    
    def __init__(self, message: str = "Document processing failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)


class ParsingError(DocumentProcessingError):
    """Raised when document parsing fails."""
    
    def __init__(self, message: str = "Failed to parse document", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details=details)


class ChunkingError(DocumentProcessingError):
    """Raised when document chunking fails."""
    
    def __init__(self, message: str = "Failed to chunk document", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details=details)


# Database Exceptions
class DatabaseError(RAGEdtechException):
    """Raised when database operation fails."""
    
    def __init__(self, message: str = "Database error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)


class ResourceNotFoundError(RAGEdtechException):
    """Raised when requested resource is not found."""
    
    def __init__(self, resource: str, resource_id: str, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details['resource'] = resource
        details['resource_id'] = resource_id
        message = f"{resource} with ID {resource_id} not found"
        super().__init__(message, status_code=404, details=details)


# Security Exceptions
class PromptInjectionError(RAGEdtechException):
    """Raised when potential prompt injection is detected."""
    
    def __init__(self, message: str = "Potential security threat detected", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)


class SecurityError(RAGEdtechException):
    """Raised for general security violations."""
    
    def __init__(self, message: str = "Security error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=403, details=details)


# Cache Exceptions
class CacheError(RAGEdtechException):
    """Raised when cache operation fails."""
    
    def __init__(self, message: str = "Cache operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)


# Queue Exceptions
class QueueError(RAGEdtechException):
    """Raised when message queue operation fails."""
    
    def __init__(self, message: str = "Queue operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)

