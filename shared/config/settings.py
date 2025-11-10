"""
Centralized configuration management using Pydantic BaseSettings.
Reads from environment variables with validation.
"""
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, ValidationError
from typing import Optional
from shared.logging.logger import get_logger

logger = get_logger("settings")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Service Configuration
    service_name: str = Field(default="rag-edtech-service", env="SERVICE_NAME")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # MongoDB Configuration
    mongodb_url: str = Field(..., env="MONGODB_URL")
    mongodb_database: str = Field(default="rag_edtech", env="MONGO_DATABASE")
    
    # Redis Configuration
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    
    # RabbitMQ Configuration
    rabbitmq_url: Optional[str] = Field(default=None, env="RABBITMQ_URL")
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # Pinecone Configuration
    pinecone_api_key: Optional[str] = Field(default=None, env="PINECONE_API_KEY")
    pinecone_environment: Optional[str] = Field(default=None, env="PINECONE_ENVIRONMENT")
    pinecone_index_name: str = Field(default="edtech-rag-index", env="PINECONE_INDEX_NAME")
    
    # Langfuse Configuration
    langfuse_public_key: Optional[str] = Field(default=None, env="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: Optional[str] = Field(default=None, env="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(default="https://cloud.langfuse.com", env="LANGFUSE_HOST")
    
    # JWT Configuration
    jwt_secret: str = Field(..., env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, env="ACCESS_TOKEN_EXPIRE_MINUTES")  # 15 minutes as per documentation
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Application Configuration
    max_file_size_mb: int = Field(default=50, env="MAX_FILE_SIZE_MB")
    chunk_size: int = Field(default=512, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, env="CHUNK_OVERLAP")
    
    # LLM Configuration
    llm_model: str = Field(default="gpt-4", env="LLM_MODEL")
    embedding_model: str = Field(default="text-embedding-3-large", env="EMBEDDING_MODEL")
    top_k_results: int = Field(default=5, env="TOP_K_RESULTS")
    
    # Rate Limiting
    rate_limit_per_user: int = Field(default=100, env="RATE_LIMIT_PER_USER")
    rate_limit_global: int = Field(default=1000, env="RATE_LIMIT_GLOBAL")
    rate_limit_window_hours: int = Field(default=1, env="RATE_LIMIT_WINDOW_HOURS")
    
    # Cache Configuration
    cache_ttl_seconds: int = Field(default=3600, env="CACHE_TTL_SECONDS")
    
    # Service URLs (for API Gateway)
    auth_service_url: Optional[str] = Field(default=None, env="AUTH_SERVICE_URL")
    document_processor_url: Optional[str] = Field(default=None, env="DOCUMENT_PROCESSOR_URL")
    vectorization_service_url: Optional[str] = Field(default=None, env="VECTORIZATION_SERVICE_URL")
    rag_query_service_url: Optional[str] = Field(default=None, env="RAG_QUERY_SERVICE_URL")
    analytics_service_url: Optional[str] = Field(default=None, env="ANALYTICS_SERVICE_URL")
    
    # CORS Configuration
    cors_origins: str = Field(default="http://localhost:3000", env="CORS_ORIGINS")
    
    @field_validator('jwt_secret')
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Validate JWT secret is at least 32 characters."""
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return v
    
    @field_validator('access_token_expire_minutes')
    @classmethod
    def validate_access_token_expiry(cls, v: int) -> int:
        """Validate access token expiry is reasonable."""
        if v < 1 or v > 1440:  # Between 1 minute and 24 hours
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be between 1 and 1440")
        return v
    
    @field_validator('max_file_size_mb')
    @classmethod
    def validate_max_file_size(cls, v: int) -> int:
        """Validate max file size is reasonable."""
        if v < 1 or v > 500:  # Between 1MB and 500MB
            raise ValueError("MAX_FILE_SIZE_MB must be between 1 and 500")
        return v
    
    def validate_service_requirements(self, service_name: str):
        """
        Validate required environment variables for specific services.
        
        Args:
            service_name: Name of the service (e.g., 'auth', 'rag-query')
        
        Raises:
            ValueError: If required variables are missing
        """
        service_requirements = {
            'auth': ['mongodb_url', 'jwt_secret'],
            'document-processor': ['mongodb_url', 'rabbitmq_url'],
            'vectorization': ['mongodb_url', 'rabbitmq_url', 'openai_api_key', 'pinecone_api_key'],
            'rag-query': ['mongodb_url', 'redis_url', 'openai_api_key', 'pinecone_api_key'],
            'analytics': ['mongodb_url', 'redis_url'],
            'api-gateway': ['jwt_secret', 'auth_service_url', 'document_processor_url', 
                          'rag_query_service_url', 'analytics_service_url']
        }
        
        required = service_requirements.get(service_name, [])
        missing = []
        
        for field in required:
            value = getattr(self, field, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(field.upper())
        
        if missing:
            raise ValueError(
                f"Missing required environment variables for {service_name}: {', '.join(missing)}"
            )
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
try:
    settings = Settings()
except ValidationError as e:
    logger.error(f"Configuration validation failed: {e}")
    raise

