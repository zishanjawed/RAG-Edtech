"""
Auth Service - Handles user authentication and authorization.
"""
from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from datetime import datetime
from uuid import UUID
from typing import Optional

from models.user import UserCreate, UserLogin, UserResponse, Token, RefreshTokenRequest, UpdateProfileRequest, ChangePasswordRequest
from security.jwt_handler import jwt_handler
from config import settings
from shared.database.mongodb_client import mongodb_client, get_mongodb
from shared.utils.security import password_hasher, input_validator
from shared.exceptions.custom_exceptions import (
    AuthenticationError,
    ValidationError,
    ResourceNotFoundError,
    InvalidTokenError
)
from shared.middleware.error_handler import register_exception_handlers
from shared.logging.logger import get_logger

logger = get_logger(settings.service_name, settings.log_level)


# Dependency to get current user from Authorization header
async def get_current_user_from_token(
    authorization: Optional[str] = Header(None),
    db=Depends(get_mongodb)
) -> dict:
    """
    Extract and validate user from Authorization header.
    
    Args:
        authorization: Authorization header (Bearer <token>)
        db: MongoDB database instance
    
    Returns:
        User document from database
    
    Raises:
        InvalidTokenError: If token is missing or invalid
        ResourceNotFoundError: If user not found
    """
    if not authorization:
        raise InvalidTokenError("Authorization header is missing")
    
    if not authorization.startswith("Bearer "):
        raise InvalidTokenError("Invalid authorization header format")
    
    token = authorization.replace("Bearer ", "").strip()
    
    # Verify access token
    try:
        payload = jwt_handler.verify_access_token(token)
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise InvalidTokenError(f"Invalid token: {str(e)}")
    
    # Get user from database
    user = await db.users.find_one({"user_id": payload['sub']})
    if not user:
        raise ResourceNotFoundError("User", payload['sub'])
    
    return user

# Create FastAPI app
app = FastAPI(
    title="RAG Edtech - Auth Service",
    description="Authentication and user management service",
    version="1.0.0"
)

# Add CORS middleware (centralized configuration)
from shared.middleware.cors_config import configure_cors
configure_cors(app, settings.cors_origins)

# Register exception handlers
register_exception_handlers(app)


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup."""
    logger.info("Starting Auth Service...")
    
    # Validate required environment variables
    try:
        settings.validate_service_requirements('auth')
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise
    
    # Connect to MongoDB
    await mongodb_client.connect(
        settings.mongodb_url,
        settings.mongodb_database
    )
    
    # Create indexes
    db = mongodb_client.get_database()
    await db.users.create_index("email", unique=True)
    await db.users.create_index("user_id")
    
    logger.info("Auth Service started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Auth Service...")
    await mongodb_client.disconnect()
    logger.info("Auth Service shut down successfully")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    mongo_healthy = await mongodb_client.health_check()
    
    return {
        "status": "healthy" if mongo_healthy else "unhealthy",
        "service": "auth-service",
        "mongodb": "connected" if mongo_healthy else "disconnected"
    }


@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db=Depends(get_mongodb)):
    """
    Register a new user.
    
    Args:
        user_data: User registration data
        db: MongoDB database instance
    
    Returns:
        Created user data (without password)
    
    Raises:
        ValidationError: If email already exists or validation fails
    """
    logger.info(f"Registration attempt for email: {user_data.email}")
    
    # Validate email
    if not input_validator.validate_email(user_data.email):
        raise ValidationError("Invalid email format")
    
    # Validate password strength
    is_valid, error_msg = input_validator.validate_password_strength(user_data.password)
    if not is_valid:
        raise ValidationError(error_msg)
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise ValidationError(
            "User with this email already exists",
            details={"email": user_data.email}
        )
    
    # Hash password
    password_hash = password_hasher.hash_password(user_data.password)
    
    # Create user document
    from models.user import UserInDB
    user_in_db = UserInDB(
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role,
        password_hash=password_hash
    )
    
    # Insert into database
    user_dict = user_in_db.model_dump()
    user_dict['user_id'] = str(user_dict['user_id'])
    
    await db.users.insert_one(user_dict)
    
    logger.info(f"User registered successfully: {user_data.email}")
    
    # Return user response (without password hash)
    return UserResponse(**user_in_db.model_dump())


@app.post("/auth/login", response_model=Token, response_model_exclude_none=False)
async def login(credentials: UserLogin, db=Depends(get_mongodb)):
    """
    Authenticate user and return tokens.
    
    Args:
        credentials: Login credentials
        db: MongoDB database instance
    
    Returns:
        Access and refresh tokens
    
    Raises:
        AuthenticationError: If credentials are invalid
    """
    logger.info(f"Login attempt for email: {credentials.email}")
    
    # Find user by email
    user = await db.users.find_one({"email": credentials.email})
    if not user:
        logger.warning(f"Login failed: User not found - {credentials.email}")
        raise AuthenticationError("Invalid email or password")
    
    # Verify password
    if not password_hasher.verify_password(credentials.password, user['password_hash']):
        logger.warning(f"Login failed: Invalid password - {credentials.email}")
        raise AuthenticationError("Invalid email or password")
    
    # Check if user is active
    if not user.get('is_active', True):
        logger.warning(f"Login failed: User inactive - {credentials.email}")
        raise AuthenticationError("Account is inactive")
    
    # Update last login
    await db.users.update_one(
        {"email": credentials.email},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Create tokens
    access_token = jwt_handler.create_access_token(
        user_id=user['user_id'],
        email=user['email'],
        role=user['role']
    )
    
    refresh_token = jwt_handler.create_refresh_token(
        user_id=user['user_id'],
        email=user['email'],
        role=user['role']
    )
    
    logger.info(f"Login successful: {credentials.email}")
    
    # Prepare user object (exclude password_hash)
    user_obj = {
        "id": user['user_id'],
        "email": user['email'],
        "full_name": user['full_name'],
        "role": user['role'],
        "createdAt": user['created_at'].isoformat() if 'created_at' in user else None,
        "updatedAt": user.get('last_login').isoformat() if user.get('last_login') else None
    }
    
    logger.info(f"User object: {user_obj}")
    
    token_response = Token(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_obj
    )
    
    logger.info(f"Token response: {token_response.model_dump()}")
    
    return token_response


@app.post("/auth/refresh", response_model=Token)
async def refresh_token(request: RefreshTokenRequest, db=Depends(get_mongodb)):
    """
    Refresh access token using refresh token.
    
    Args:
        request: Refresh token request with refresh_token field
        db: MongoDB database instance
    
    Returns:
        New access and refresh tokens
    
    Raises:
        InvalidTokenError: If refresh token is invalid
    """
    # Verify refresh token
    payload = jwt_handler.verify_refresh_token(request.refresh_token)
    
    # Get user from database
    user = await db.users.find_one({"user_id": payload['sub']})
    if not user or not user.get('is_active', True):
        raise AuthenticationError("Invalid token or inactive user")
    
    # Create new tokens
    new_access_token = jwt_handler.create_access_token(
        user_id=user['user_id'],
        email=user['email'],
        role=user['role']
    )
    
    new_refresh_token = jwt_handler.create_refresh_token(
        user_id=user['user_id'],
        email=user['email'],
        role=user['role']
    )
    
    logger.info(f"Token refreshed for user: {user['email']}")
    
    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token
    )


@app.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user_from_token)):
    """
    Get current user information from Authorization header.
    
    Args:
        current_user: Current user from token dependency
    
    Returns:
        Current user data
    """
    return UserResponse(**current_user)


@app.patch("/auth/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user_from_token),
    db=Depends(get_mongodb)
):
    """
    Update user profile information (name only).
    
    Args:
        profile_data: Profile update data (full_name)
        current_user: Current user from token dependency
        db: MongoDB database instance
    
    Returns:
        Updated user data
    
    Raises:
        ValidationError: If validation fails
    """
    user_id = current_user['user_id']
    
    # Build update dict (only include provided fields)
    update_data = {}
    if profile_data.full_name is not None:
        update_data['full_name'] = profile_data.full_name
    
    if not update_data:
        raise ValidationError("No fields to update")
    
    # Update user
    update_data['updated_at'] = datetime.utcnow()
    
    result = await db.users.find_one_and_update(
        {"user_id": user_id},
        {"$set": update_data},
        return_document=True
    )
    
    if not result:
        raise ResourceNotFoundError("User", user_id)
    
    logger.info(f"Profile updated for user: {result['email']}")
    
    return UserResponse(**result)


@app.post("/auth/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user_from_token),
    db=Depends(get_mongodb)
):
    """
    Change user password.
    
    Args:
        password_data: Password change data
        current_user: Current user from token dependency
        db: MongoDB database instance
    
    Returns:
        Success message
    
    Raises:
        AuthenticationError: If current password is incorrect
        ValidationError: If new password is invalid
    """
    user_id = current_user['user_id']
    
    # Verify current password
    if not password_hasher.verify_password(
        password_data.current_password,
        current_user['password_hash']
    ):
        raise AuthenticationError("Current password is incorrect")
    
    # Validate new password strength
    is_valid, error_msg = input_validator.validate_password_strength(
        password_data.new_password
    )
    if not is_valid:
        raise ValidationError(error_msg)
    
    # Hash new password
    new_password_hash = password_hasher.hash_password(password_data.new_password)
    
    # Update password
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {
            "password_hash": new_password_hash,
            "updated_at": datetime.utcnow()
        }}
    )
    
    logger.info(f"Password changed for user: {current_user['email']}")
    
    return {"message": "Password updated successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

