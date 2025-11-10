"""
Unit tests for Auth Service.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from main import app
from shared.utils.security import password_hasher


@pytest.fixture
def client():
    """Test client for Auth Service."""
    return TestClient(app)


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB database."""
    mock_db = MagicMock()
    mock_db.users = MagicMock()
    return mock_db


def test_password_hashing():
    """Test 1: Password hashing and verification."""
    password = "SecurePassword123!"
    hashed = password_hasher.hash_password(password)
    
    # Verify hash is created
    assert hashed is not None
    assert hashed != password
    
    # Verify password verification works
    assert password_hasher.verify_password(password, hashed) is True
    assert password_hasher.verify_password("WrongPassword", hashed) is False


@pytest.mark.asyncio
async def test_user_registration_validation():
    """Test 2: User registration with validation."""
    from shared.utils.security import input_validator
    
    # Test valid email
    assert input_validator.validate_email("test@example.com") is True
    assert input_validator.validate_email("invalid-email") is False
    
    # Test password strength
    is_valid, error = input_validator.validate_password_strength("weak")
    assert is_valid is False
    assert error is not None
    
    is_valid, error = input_validator.validate_password_strength("Strong1Pass!")
    assert is_valid is True
    assert error is None


def test_jwt_token_creation():
    """Test 3: JWT token creation and validation."""
    from security.jwt_handler import jwt_handler
    
    # Create tokens
    user_id = "test-user-123"
    email = "test@example.com"
    role = "student"
    
    access_token = jwt_handler.create_access_token(user_id, email, role)
    refresh_token = jwt_handler.create_refresh_token(user_id, email, role)
    
    # Verify tokens are created
    assert access_token is not None
    assert refresh_token is not None
    assert access_token != refresh_token
    
    # Verify access token can be decoded
    payload = jwt_handler.verify_access_token(access_token)
    assert payload['sub'] == user_id
    assert payload['email'] == email
    assert payload['role'] == role
    assert payload['type'] == 'access'
    
    # Verify refresh token can be decoded
    payload = jwt_handler.verify_refresh_token(refresh_token)
    assert payload['type'] == 'refresh'


@pytest.mark.asyncio
async def test_invalid_token_rejection():
    """Test 4: Invalid token should be rejected."""
    from security.jwt_handler import jwt_handler
    from shared.exceptions.custom_exceptions import InvalidTokenError
    
    # Test with invalid token
    with pytest.raises(InvalidTokenError):
        jwt_handler.verify_access_token("invalid.token.here")
    
    # Test with refresh token on access verification
    refresh_token = jwt_handler.create_refresh_token("user", "email@test.com", "student")
    with pytest.raises(InvalidTokenError):
        jwt_handler.verify_access_token(refresh_token)

