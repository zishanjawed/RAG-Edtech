"""
Security utilities for password hashing and validation.
"""
import bcrypt
import re
from typing import Optional
from shared.exceptions.custom_exceptions import ValidationError, PromptInjectionError


class PasswordHasher:
    """Password hashing utilities using bcrypt."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
        
        Returns:
            Hashed password
        """
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
        
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False


class InputValidator:
    """Input validation and sanitization utilities."""
    
    # Patterns that might indicate prompt injection
    SUSPICIOUS_PATTERNS = [
        # Direct instruction manipulation
        r'ignore\s+(previous|above|prior|all)\s+(instructions?|prompts?|commands?)',
        r'disregard\s+(previous|above|prior|all)',
        r'forget\s+(everything|all|previous|prior)\s+(instructions?|prompts?)',
        r'new\s+(instructions?|prompts?|commands?)\s*:',
        
        # System prompt exposure attempts
        r'system:?\s*(you\s+are|prompt|message)',
        r'show\s+(me\s+)?(your\s+)?(system\s+)?(prompt|instructions?)',
        r'what\s+(is|are)\s+your\s+(system\s+)?(prompt|instructions?)',
        r'reveal\s+your\s+(prompt|instructions?|system)',
        
        # Role manipulation
        r'you\s+are\s+now\s+(a|an)',
        r'act\s+as\s+(a|an|if)',
        r'pretend\s+(you\s+are|to\s+be)',
        r'roleplay\s+as',
        r'simulate\s+(being\s+)?a',
        
        # Special tokens and markers
        r'<\s*\|im_start\|',
        r'<\s*\|im_end\|',
        r'<\s*\|endoftext\|',
        r'###\s*(instruction|human|assistant|system)',
        r'\[INST\]',
        r'\[/INST\]',
        
        # Jailbreak attempts
        r'jailbreak',
        r'do\s+anything\s+now',
        r'DAN\s+mode',
        r'developer\s+mode',
        r'unrestricted',
        
        # Output manipulation
        r'output\s+(only|just)',
        r'respond\s+with\s+(only|just)',
        r'answer\s+in\s+the\s+format',
        
        # Encoding bypass attempts
        r'base64',
        r'rot13',
        r'hex\s+encode',
        r'\\x[0-9a-f]{2}',  # Hex escape sequences
    ]
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format.
        
        Args:
            email: Email address
        
        Returns:
            True if valid, False otherwise
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        return True, None
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 500) -> str:
        """
        Sanitize user input by removing potentially harmful characters.
        
        Args:
            text: Input text
            max_length: Maximum allowed length
        
        Returns:
            Sanitized text
        
        Raises:
            ValidationError: If input is too long
        """
        if len(text) > max_length:
            raise ValidationError(
                f"Input too long. Maximum {max_length} characters allowed.",
                details={"max_length": max_length, "provided_length": len(text)}
            )
        
        # Remove control characters except newlines and tabs
        sanitized = ''.join(char for char in text if char.isprintable() or char in '\n\t')
        
        return sanitized.strip()
    
    @staticmethod
    def detect_prompt_injection(text: str) -> bool:
        """
        Detect potential prompt injection attempts.
        
        Args:
            text: Input text to check
        
        Returns:
            True if suspicious patterns detected, False otherwise
        """
        text_lower = text.lower()
        
        for pattern in InputValidator.SUSPICIOUS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        return False
    
    @staticmethod
    def validate_question(question: str, max_length: int = 500):
        """
        Validate and sanitize a question input.
        
        Args:
            question: Question text
            max_length: Maximum allowed length
        
        Returns:
            Sanitized question
        
        Raises:
            ValidationError: If question is invalid
            PromptInjectionError: If injection detected
        """
        # Sanitize input
        sanitized = InputValidator.sanitize_input(question, max_length)
        
        # Check for prompt injection
        if InputValidator.detect_prompt_injection(sanitized):
            raise PromptInjectionError(
                "Your input contains patterns that are not allowed for security reasons.",
                details={"input_length": len(question)}
            )
        
        # Ensure question is not empty
        if not sanitized:
            raise ValidationError("Question cannot be empty")
        
        return sanitized


# Create instances for easy import
password_hasher = PasswordHasher()
input_validator = InputValidator()

