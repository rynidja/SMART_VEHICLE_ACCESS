from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum

# Enums
class UserRole(str, Enum):
    """User roles for RBAC system."""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"

# schemas
class Token(BaseModel):
    """JWT token response schema."""
    access_token: str = Field(...)
    token_type: str = Field(default="bearer")
    expires_in: Optional[int] = Field(default=3600)

class LoginRequest(BaseModel):
    """User login request schema."""
    username: str = Field(...)
    password: str = Field(...)

class UserBase(BaseModel):
    """Base user schema shared across other schemas."""
    username: str = Field(..., max_length=50)
    email: EmailStr
    role: Optional[UserRole] = Field(default=UserRole.VIEWER)
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=6)

class UserUpdate(BaseModel):
    """Schema for updating user details."""
    username: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    """Schema for user data returned to clients."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True
