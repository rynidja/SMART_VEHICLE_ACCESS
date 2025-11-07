# Authentication API router
# Handles user login, token management, and authentication

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import logging

from backend.database import get_async_db
from backend.models import User
from backend.core.security import (
    verify_password, get_password_hash, create_access_token, 
    verify_token, check_permission
)
from backend.schemas.auth import Token, LoginRequest, UserCreate, UserResponse, UserUpdate, UserRole

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Authenticate user and return access token.
    
    Args:
        form_data: OAuth2 password form data
        db: Database session
        
    Returns:
        Token: Access token and metadata
    """
    try:
        # Find user by username
        result = await db.execute(
            select(User).where(User.username == form_data.username)
        )
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(form_data.password, user.hashed_password):
            logger.warning(f"Failed login attempt for username: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        await db.commit()
        
        # Create access token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id, "role": user.role},
            expires_delta=access_token_expires
        )
        
        logger.info(f"User {user.username} logged in successfully")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": int(access_token_expires.total_seconds())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(verify_token)
):
    """
    Register a new user (admin only).
    
    Args:
        user_data: User registration data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        UserResponse: Created user data
    """
    try:
        # Check if current user has admin role
        if not check_permission(current_user.get("role"), UserRole.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can create new users"
            )
        
        # Check if username already exists
        existing_user = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        existing_email = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing_email.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            role=user_data.role,
            is_active=user_data.is_active
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        logger.info(f"New user created: {user_data.username} by {current_user.get('username')}")
        
        return UserResponse.from_orm(new_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        UserResponse: Current user data
    """
    try:
        result = await db.execute(
            select(User).where(User.id == current_user.get("user_id"))
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user information"
        )

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update current user information.
    
    Args:
        user_data: Updated user data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        UserResponse: Updated user data
    """
    try:
        result = await db.execute(
            select(User).where(User.id == current_user.get("user_id"))
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields
        update_data = user_data.dict(exclude_unset=True)
        
        # Handle password update
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        # Check for username/email conflicts
        if "username" in update_data:
            existing_user = await db.execute(
                select(User).where(
                    User.username == update_data["username"],
                    User.id != user.id
                )
            )
            if existing_user.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        if "email" in update_data:
            existing_email = await db.execute(
                select(User).where(
                    User.email == update_data["email"],
                    User.id != user.id
                )
            )
            if existing_email.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already taken"
                )
        
        # Apply updates
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"User {user.username} updated their profile")
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user information"
        )

@router.get("/users", response_model=list[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get list of users (admin only).
    
    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[UserResponse]: List of users
    """
    try:
        # Check if current user has admin role
        if not check_permission(current_user.get("role"), UserRole.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can view user list"
            )
        
        result = await db.execute(
            select(User).offset(skip).limit(limit)
        )
        users = result.scalars().all()
        
        return [UserResponse.from_orm(user) for user in users]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users"
        )

# TODO: add jwt black list
@router.post("/logout")
async def logout(current_user: dict = Depends(verify_token)):
    """
    Logout user (client should discard token).
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        dict: Success message
    """
    logger.info(f"User {current_user.get('username')} logged out")
    return {"message": "Successfully logged out"}
