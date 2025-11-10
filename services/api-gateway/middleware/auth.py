"""
Authentication middleware for JWT validation.
"""
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from shared.exceptions.custom_exceptions import AuthenticationError, InvalidTokenError
from shared.logging.logger import get_logger
from jose import JWTError, jwt
from config import settings

logger = get_logger("auth_middleware")

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Extract and validate JWT token from request.
    
    Args:
        credentials: HTTP Authorization credentials
    
    Returns:
        Token payload with user information
    
    Raises:
        AuthenticationError: If token is invalid
    """
    token = credentials.credentials
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Verify token type
        if payload.get("type") != "access":
            raise InvalidTokenError("Not an access token")
        
        # Extract user information
        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")
        
        if not user_id or not email:
            raise InvalidTokenError("Invalid token payload")
        
        return {
            "user_id": user_id,
            "email": email,
            "role": role
        }
        
    except JWTError as e:
        logger.error(f"JWT validation failed: {str(e)}")
        raise InvalidTokenError(
            "Invalid or expired token",
            details={"error": str(e)}
        )


async def get_optional_user(
    request: Request
) -> Optional[Dict[str, Any]]:
    """
    Extract user from token if present, but don't require it.
    
    Args:
        request: FastAPI request
    
    Returns:
        Token payload or None
    """
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        
        if payload.get("type") == "access":
            return {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "role": payload.get("role")
            }
    except JWTError:
        pass
    
    return None


def require_role(required_role: str):
    """
    Dependency to require specific user role.
    
    Args:
        required_role: Required role (e.g., "teacher", "student")
    
    Returns:
        Dependency function
    """
    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        if current_user.get("role") != required_role:
            raise AuthenticationError(
                f"Access denied. Required role: {required_role}",
                details={"required_role": required_role, "user_role": current_user.get("role")}
            )
        return current_user
    
    return role_checker

