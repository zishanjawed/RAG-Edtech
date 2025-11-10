"""
Structured logging configuration for all services.
Provides JSON-formatted logs with consistent structure.
"""
import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add service name from environment or record
        if hasattr(record, 'service_name'):
            log_record['service_name'] = record.service_name
        
        # Add trace ID if available
        if hasattr(record, 'trace_id'):
            log_record['trace_id'] = record.trace_id


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Set up a logger with JSON formatting.
    
    Args:
        name: Logger name (usually service name)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))
    
    # Create JSON formatter
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds contextual information to all log records.
    """
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Add extra fields to log record."""
        # Add service name if available
        if 'service_name' in self.extra:
            kwargs.setdefault('extra', {})['service_name'] = self.extra['service_name']
        
        # Add trace ID if available
        if 'trace_id' in self.extra:
            kwargs.setdefault('extra', {})['trace_id'] = self.extra['trace_id']
        
        return msg, kwargs


def get_logger(service_name: str, level: str = "INFO", trace_id: str = None) -> logging.Logger:
    """
    Get a logger with contextual information.
    
    Args:
        service_name: Name of the service
        level: Log level
        trace_id: Optional trace ID for request tracking
    
    Returns:
        Logger instance with adapters
    """
    logger = setup_logger(service_name, level)
    
    extra = {'service_name': service_name}
    if trace_id:
        extra['trace_id'] = trace_id
    
    return LoggerAdapter(logger, extra)

