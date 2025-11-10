"""
JWT token generation and validation.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from shared.exceptions.custom_exceptions import InvalidTokenError, AuthenticationError
from shared.config.settings import settings


class JWTHandler:
    """Handle JWT token creation and validation."""
    
    @staticmethod
    def create_access_token(
        user_id: str,
        email: str,
        role: str
    ) -> str:
        """
        Create an access token.
        
        Args:
            user_id: User ID
            email: User email
            role: User role
        
        Returns:
            Encoded JWT token
        """
        now = datetime.utcnow()
        expire = now + timedelta(
            minutes=settings.access_token_expire_minutes
        )
        
        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "exp": expire,
            "iat": now,  # Issued at time
            "type": "access"
        }
        
        return jwt.encode(
            payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm
        )
    
    @staticmethod
    def create_refresh_token(
        user_id: str,
        email: str,
        role: str
    ) -> str:
        """
        Create a refresh token.
        
        Args:
            user_id: User ID
            email: User email
            role: User role
        
        Returns:
            Encoded JWT token
        """
        now = datetime.utcnow()
        expire = now + timedelta(
            days=settings.refresh_token_expire_days
        )
        
        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "exp": expire,
            "iat": now,  # Issued at time
            "type": "refresh"
        }
        
        return jwt.encode(
            payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm
        )
    
    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token to decode
        
        Returns:
            Token payload
        
        Raises:
            InvalidTokenError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm]
            )
            return payload
        except JWTError as e:
            raise InvalidTokenError(
                "Invalid or expired token",
                details={"error": str(e)}
            )
    
    @staticmethod
    def verify_access_token(token: str) -> Dict[str, Any]:
        """
        Verify an access token.
        
        Args:
            token: JWT access token
        
        Returns:
            Token payload
        
        Raises:
            InvalidTokenError: If token is invalid or not an access token
        """
        payload = JWTHandler.decode_token(token)
        
        if payload.get("type") != "access":
            raise InvalidTokenError("Not an access token")
        
        return payload
    
    @staticmethod
    def verify_refresh_token(token: str) -> Dict[str, Any]:
        """
        Verify a refresh token.
        
        Args:
            token: JWT refresh token
        
        Returns:
            Token payload
        
        Raises:
            InvalidTokenError: If token is invalid or not a refresh token
        """
        payload = JWTHandler.decode_token(token)
        
        if payload.get("type") != "refresh":
            raise InvalidTokenError("Not a refresh token")
        
        return payload


# Create instance
jwt_handler = JWTHandler()

