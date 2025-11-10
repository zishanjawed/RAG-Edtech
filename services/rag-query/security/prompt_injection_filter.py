"""
Security filters to prevent prompt injection attacks.
"""
from shared.utils.security import input_validator
from shared.exceptions.custom_exceptions import PromptInjectionError, ValidationError
from shared.logging.logger import get_logger

logger = get_logger("prompt_injection_filter")


class PromptInjectionFilter:
    """Filter to detect and prevent prompt injection attempts."""
    
    @staticmethod
    def validate_question(question: str, max_length: int = 500) -> str:
        """
        Validate and sanitize a question.
        
        Args:
            question: Question text
            max_length: Maximum allowed length
        
        Returns:
            Sanitized question
        
        Raises:
            ValidationError: If question is invalid
            PromptInjectionError: If injection detected
        """
        # Use shared input validator
        sanitized = input_validator.validate_question(question, max_length)
        
        logger.debug(f"Question validated and sanitized (length: {len(sanitized)})")
        
        return sanitized
    
    @staticmethod
    def check_response_safety(response: str) -> bool:
        """
        Check if generated response is safe (doesn't leak system prompts).
        
        Args:
            response: Generated response
        
        Returns:
            True if safe, False otherwise
        """
        # Check for system prompt leakage
        unsafe_patterns = [
            "You are an expert IB Chemistry tutor",
            "SYSTEM:",
            "<|im_start|>",
            "<|im_end|>"
        ]
        
        response_lower = response.lower()
        
        for pattern in unsafe_patterns:
            if pattern.lower() in response_lower:
                logger.warning(f"Unsafe response detected: contains '{pattern}'")
                return False
        
        return True

