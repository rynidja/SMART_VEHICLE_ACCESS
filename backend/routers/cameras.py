# Camera management API router
# Handles camera configuration, status monitoring, and stream management

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime
import logging

from backend.database import get_async_db
from backend.models.database import Camera, CameraStatus
from backend.core.security import verify_token, check_permission, UserRole
from backend.schemas.camera import (
    CameraCreate, CameraUpdate, CameraResponse, CameraStatsResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=CameraResponse)
async def create_camera(
    camera_data: CameraCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(verify_token)
):
    """
    Create a new camera configuration.
    
    Args:
        camera_data: Camera configuration data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        CameraResponse: Created camera data
    """
    try:
        # Check if user has operator or admin role
        if not check_permission(current_user.get("role"), UserRole.OPERATOR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only operators and administrators can create cameras"
            )
        
        # Check if camera name already exists
        existing_camera = await db.execute(
            select(Camera).where(Camera.name == camera_data.name)
        )
        if existing_camera.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Camera name already exists"
            )
        
        # Create new camera
        new_camera = Camera(
            name=camera_data.name,
            description=camera_data.description,
            location=camera_data.location,
            stream_url=camera_data.stream_url,
            stream_type=camera_data.stream_type,
            fps=camera_data.fps,
            resolution_width=camera_data.resolution_width,
            resolution_height=camera_data.resolution_height,
            status=camera_data.status,
            is_enabled=camera_data.is_enabled,
            roi_x=camera_data.roi_x,
            roi_y=camera_data.roi_y,
            roi_width=camera_data.roi_width,
            roi_height=camera_data.roi_height
        )
        
        db.add(new_camera)
        await db.commit()
        await db.refresh(new_camera)
        
        logger.info(f"Created camera: {camera_data.name} by user {current_user.get('username')}")
        
        return CameraResponse.from_orm(new_camera)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating camera: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create camera"
        )

@router.get("/", response_model=List[CameraResponse])
async def get_cameras(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[CameraStatus] = None,
    is_enabled: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get list of cameras with optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by camera status
        is_enabled: Filter by enabled status
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List[CameraResponse]: List of cameras
    """
    try:
        query = select(Camera)
        
        # Apply filters
        filters = []
        if status is not None:
            filters.append(Camera.status == status)
        if is_enabled is not None:
            filters.append(Camera.is_enabled == is_enabled)
        
        if filters:
            query = query.where(and_(*filters))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        cameras = result.scalars().all()
        
        return [CameraResponse.from_orm(camera) for camera in cameras]
        
    except Exception as e:
        logger.error(f"Error fetching cameras: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch cameras"
        )

@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get a specific camera by ID.
    
    Args:
        camera_id: Camera ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        CameraResponse: Camera data
    """
    try:
        result = await db.execute(
            select(Camera).where(Camera.id == camera_id)
        )
        camera = result.scalar_one_or_none()
        
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Camera not found"
            )
        
        return CameraResponse.from_orm(camera)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching camera {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch camera"
        )

@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: int,
    camera_data: CameraUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(verify_token)
):
    """
    Update camera configuration.
    
    Args:
        camera_id: Camera ID
        camera_data: Updated camera data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        CameraResponse: Updated camera data
    """
    try:
        # Check if user has operator or admin role
        if not check_permission(current_user.get("role"), UserRole.OPERATOR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only operators and administrators can update cameras"
            )
        
        result = await db.execute(
            select(Camera).where(Camera.id == camera_id)
        )
        camera = result.scalar_one_or_none()
        
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Camera not found"
            )
        
        # Check for name conflicts if name is being updated
        if camera_data.name and camera_data.name != camera.name:
            existing_camera = await db.execute(
                select(Camera).where(
                    Camera.name == camera_data.name,
                    Camera.id != camera_id
                )
            )
            if existing_camera.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Camera name already exists"
                )
        
        # Update fields
        update_data = camera_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(camera, field, value)
        
        # Update timestamp
        camera.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(camera)
        
        logger.info(f"Updated camera {camera_id} by user {current_user.get('username')}")
        
        return CameraResponse.from_orm(camera)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating camera {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update camera"
        )

@router.delete("/{camera_id}")
async def delete_camera(
    camera_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(verify_token)
):
    """
    Delete a camera configuration.
    
    Args:
        camera_id: Camera ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        dict: Success message
    """
    try:
        # Check if user has admin role
        if not check_permission(current_user.get("role"), UserRole.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can delete cameras"
            )
        
        result = await db.execute(
            select(Camera).where(Camera.id == camera_id)
        )
        camera = result.scalar_one_or_none()
        
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Camera not found"
            )
        
        await db.delete(camera)
        await db.commit()
        
        logger.info(f"Deleted camera {camera_id} by user {current_user.get('username')}")
        
        return {"message": "Camera deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting camera {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete camera"
        )

@router.post("/{camera_id}/start")
async def start_camera(
    camera_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(verify_token)
):
    """
    Start camera processing.
    
    Args:
        camera_id: Camera ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        dict: Success message
    """
    try:
        # Check if user has operator or admin role
        if not check_permission(current_user.get("role"), UserRole.OPERATOR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only operators and administrators can start cameras"
            )
        
        result = await db.execute(
            select(Camera).where(Camera.id == camera_id)
        )
        camera = result.scalar_one_or_none()
        
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Camera not found"
            )
        
        if not camera.is_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Camera is disabled"
            )
        
        # Update camera status
        camera.status = CameraStatus.ACTIVE
        camera.updated_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"Started camera {camera_id} by user {current_user.get('username')}")
        
        return {"message": "Camera started successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting camera {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start camera"
        )

@router.post("/{camera_id}/stop")
async def stop_camera(
    camera_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(verify_token)
):
    """
    Stop camera processing.
    
    Args:
        camera_id: Camera ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        dict: Success message
    """
    try:
        # Check if user has operator or admin role
        if not check_permission(current_user.get("role"), UserRole.OPERATOR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only operators and administrators can stop cameras"
            )
        
        result = await db.execute(
            select(Camera).where(Camera.id == camera_id)
        )
        camera = result.scalar_one_or_none()
        
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Camera not found"
            )
        
        # Update camera status
        camera.status = CameraStatus.INACTIVE
        camera.updated_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"Stopped camera {camera_id} by user {current_user.get('username')}")
        
        return {"message": "Camera stopped successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping camera {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop camera"
        )

@router.get("/stats/summary", response_model=CameraStatsResponse)
async def get_camera_stats(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get camera statistics summary.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        CameraStatsResponse: Camera statistics
    """
    try:
        # Get total cameras count
        total_cameras = await db.execute(select(Camera))
        total_count = len(total_cameras.scalars().all())
        
        # Get active cameras count
        active_cameras = await db.execute(
            select(Camera).where(Camera.status == CameraStatus.ACTIVE)
        )
        active_count = len(active_cameras.scalars().all())
        
        # Get enabled cameras count
        enabled_cameras = await db.execute(
            select(Camera).where(Camera.is_enabled == True)
        )
        enabled_count = len(enabled_cameras.scalars().all())
        
        # Get cameras by status
        status_counts = {}
        for status in CameraStatus:
            result = await db.execute(
                select(Camera).where(Camera.status == status)
            )
            status_counts[status.value] = len(result.scalars().all())
        
        return CameraStatsResponse(
            total_cameras=total_count,
            active_cameras=active_count,
            enabled_cameras=enabled_count,
            status_counts=status_counts,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error fetching camera statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch camera statistics"
        )

@router.get("/{camera_id}/health")
async def get_camera_health(
    camera_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get camera health status.
    
    Args:
        camera_id: Camera ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        dict: Camera health information
    """
    try:
        result = await db.execute(
            select(Camera).where(Camera.id == camera_id)
        )
        camera = result.scalar_one_or_none()
        
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Camera not found"
            )
        
        # In a real implementation, this would check actual camera connectivity
        # For now, we'll return basic status information
        health_status = {
            "camera_id": camera_id,
            "name": camera.name,
            "status": camera.status.value,
            "is_enabled": camera.is_enabled,
            "last_seen": camera.last_seen,
            "stream_accessible": True,  # Placeholder
            "processing_active": camera.status == CameraStatus.ACTIVE,
            "timestamp": datetime.utcnow()
        }
        
        return health_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking camera health {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check camera health"
        )
