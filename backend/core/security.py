# Security utilities for authentication and authorization
# Implements HMAC-based plate hashing for privacy protection

from datetime import datetime, timedelta
from typing import Optional, Union
import hashlib
import hmac
import secrets
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token security
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash.
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password to verify against
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        str: The hashed password
    """
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        str: The encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verify and decode a JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        dict: The decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            credentials.credentials, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception

def hash_license_plate(plate_text: str) -> str:
    """
    Create HMAC-SHA256 hash of license plate for privacy protection.
    This ensures plates are stored securely and can only be matched exactly.
    
    Args:
        plate_text: The license plate text to hash
        
    Returns:
        str: HMAC-SHA256 hash of the plate
    """
    if not settings.ENABLE_PLATE_HASHING:
        return plate_text
    
    # Normalize plate text (uppercase, strip spaces)
    normalized_plate = plate_text.upper().strip().replace(" ", "")
    
    # Create HMAC hash
    hmac_hash = hmac.new(
        settings.PLATE_HASH_SALT.encode('utf-8'),
        normalized_plate.encode('utf-8'),
        hashlib.sha256
    )
    
    return hmac_hash.hexdigest()

def verify_license_plate_hash(plate_text: str, stored_hash: str) -> bool:
    """
    Verify if a license plate text matches a stored hash.
    
    Args:
        plate_text: The license plate text to verify
        stored_hash: The stored hash to compare against
        
    Returns:
        bool: True if plate matches hash, False otherwise
    """
    if not settings.ENABLE_PLATE_HASHING:
        return plate_text == stored_hash
    
    computed_hash = hash_license_plate(plate_text)
    return hmac.compare_digest(computed_hash, stored_hash)

def generate_api_key() -> str:
    """
    Generate a secure API key for external integrations.
    
    Returns:
        str: A secure random API key
    """
    return secrets.token_urlsafe(32)

def validate_api_key(api_key: str) -> bool:
    """
    Validate an API key format (basic validation).
    In production, this should check against a database of valid keys.
    
    Args:
        api_key: The API key to validate
        
    Returns:
        bool: True if key format is valid, False otherwise
    """
    # Basic format validation - should be 32+ characters
    return len(api_key) >= 32 and api_key.replace('-', '').replace('_', '').isalnum()

def check_permission(user_role: str, required_role: str) -> bool:
    """
    Check if user role has required permission level.
    
    Args:
        user_role: The user's role
        required_role: The required role level
        
    Returns:
        bool: True if user has permission, False otherwise
    """
    role_hierarchy = {
        UserRole.ADMIN: 3,
        UserRole.OPERATOR: 2,
        UserRole.VIEWER: 1
    }
    
    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level
