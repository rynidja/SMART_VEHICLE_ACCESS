# License plate API router
# Handles CRUD operations for license plates, whitelist/blacklist management

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from backend.database import get_async_db
from backend.models import LicensePlate, LicensePlateDetection, PlateStatus
from backend.core.security import verify_token, hash_license_plate, verify_license_plate_hash
from backend.schemas.plate import (
    PlateCreate, PlateUpdate, PlateResponse, PlateDetectionResponse,
    PlateSearchRequest, PlateStatsResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=PlateResponse)
async def create_plate(
    plate_data: PlateCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(verify_token)
):
    """
    Create a new license plate entry in the whitelist/blacklist.
    
    Args:
        plate_data: License plate data to create
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        PlateResponse: Created license plate data
    """
    try:
        # Hash the plate for privacy protection
        plate_hash = hash_license_plate(plate_data.plate_text)
        
        # Check if plate already exists
        existing_plate = await db.execute(
            select(LicensePlate).where(LicensePlate.plate_hash == plate_hash)
        )
        if existing_plate.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="License plate already exists"
            )
        
        # Create new plate entry
        new_plate = LicensePlate(
            plate_hash=plate_hash,
            plate_text=plate_data.plate_text,
            country_code=plate_data.country_code,
            plate_type=plate_data.plate_type,
            is_authorized=plate_data.is_authorized,
            is_blacklisted=plate_data.is_blacklisted,
            owner_name=plate_data.owner_name,
            owner_contact=plate_data.owner_contact,
            vehicle_info=plate_data.vehicle_info,
            valid_from=plate_data.valid_from,
            valid_until=plate_data.valid_until,
            created_by=current_user.get("user_id")
        )
        
        db.add(new_plate)
        await db.commit()
        await db.refresh(new_plate)
        
        logger.info(f"Created license plate: {plate_data.plate_text} by user {current_user.get('username')}")
        
        return PlateResponse.from_orm(new_plate)
        
    except Exception as e:
        logger.error(f"Error creating license plate: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create license plate"
        )

@router.get("/", response_model=List[PlateResponse])
async def get_plates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_authorized: Optional[bool] = None,
    is_blacklisted: Optional[bool] = None,
    country_code: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get list of license plates with optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        is_authorized: Filter by authorization status
        is_blacklisted: Filter by blacklist status
        country_code: Filter by country code
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List[PlateResponse]: List of license plates
    """
    try:
        query = select(LicensePlate)
        
        # Apply filters
        filters = []
        if is_authorized is not None:
            filters.append(LicensePlate.is_authorized == is_authorized)
        if is_blacklisted is not None:
            filters.append(LicensePlate.is_blacklisted == is_blacklisted)
        if country_code:
            filters.append(LicensePlate.country_code == country_code)
        
        if filters:
            query = query.where(and_(*filters))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        plates = result.scalars().all()
        
        return [PlateResponse.from_orm(plate) for plate in plates]
        
    except Exception as e:
        logger.error(f"Error fetching license plates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch license plates"
        )

@router.get("/{plate_id}", response_model=PlateResponse)
async def get_plate(
    plate_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get a specific license plate by ID.
    
    Args:
        plate_id: License plate ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        PlateResponse: License plate data
    """
    try:
        result = await db.execute(
            select(LicensePlate).where(LicensePlate.id == plate_id)
        )
        plate = result.scalar_one_or_none()
        
        if not plate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="License plate not found"
            )
        
        return PlateResponse.from_orm(plate)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching license plate {plate_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch license plate"
        )

@router.put("/{plate_id}", response_model=PlateResponse)
async def update_plate(
    plate_id: int,
    plate_data: PlateUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(verify_token)
):
    """
    Update a license plate entry.
    
    Args:
        plate_id: License plate ID
        plate_data: Updated license plate data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        PlateResponse: Updated license plate data
    """
    try:
        result = await db.execute(
            select(LicensePlate).where(LicensePlate.id == plate_id)
        )
        plate = result.scalar_one_or_none()
        
        if not plate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="License plate not found"
            )
        
        # Update fields
        update_data = plate_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(plate, field, value)
        
        # Update timestamp
        plate.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(plate)
        
        logger.info(f"Updated license plate {plate_id} by user {current_user.get('username')}")
        
        return PlateResponse.from_orm(plate)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating license plate {plate_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update license plate"
        )

@router.delete("/{plate_id}")
async def delete_plate(
    plate_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(verify_token)
):
    """
    Delete a license plate entry.
    
    Args:
        plate_id: License plate ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        dict: Success message
    """
    try:
        result = await db.execute(
            select(LicensePlate).where(LicensePlate.id == plate_id)
        )
        plate = result.scalar_one_or_none()
        
        if not plate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="License plate not found"
            )
        
        await db.delete(plate)
        await db.commit()
        
        logger.info(f"Deleted license plate {plate_id} by user {current_user.get('username')}")
        
        return {"message": "License plate deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting license plate {plate_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete license plate"
        )

@router.post("/search", response_model=List[PlateResponse])
async def search_plates(
    search_request: PlateSearchRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(verify_token)
):
    """
    Search license plates by text or other criteria.
    
    Args:
        search_request: Search criteria
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List[PlateResponse]: Matching license plates
    """
    try:
        query = select(LicensePlate)
        
        # Build search conditions
        conditions = []
        
        if search_request.plate_text:
            # Search by plate text (case insensitive)
            conditions.append(
                LicensePlate.plate_text.ilike(f"%{search_request.plate_text}%")
            )
        
        if search_request.owner_name:
            conditions.append(
                LicensePlate.owner_name.ilike(f"%{search_request.owner_name}%")
            )
        
        if search_request.country_code:
            conditions.append(LicensePlate.country_code == search_request.country_code)
        
        if search_request.plate_type:
            conditions.append(LicensePlate.plate_type == search_request.plate_type)
        
        if conditions:
            query = query.where(or_(*conditions))
        
        # Apply pagination
        query = query.offset(search_request.skip).limit(search_request.limit)
        
        result = await db.execute(query)
        plates = result.scalars().all()
        
        return [PlateResponse.from_orm(plate) for plate in plates]
        
    except Exception as e:
        logger.error(f"Error searching license plates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search license plates"
        )

@router.get("/stats/summary", response_model=PlateStatsResponse)
async def get_plate_stats(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get license plate statistics summary.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        PlateStatsResponse: License plate statistics
    """
    try:
        # Get total counts
        total_plates = await db.execute(select(LicensePlate))
        total_count = len(total_plates.scalars().all())
        
        authorized_plates = await db.execute(
            select(LicensePlate).where(LicensePlate.is_authorized == True)
        )
        authorized_count = len(authorized_plates.scalars().all())
        
        blacklisted_plates = await db.execute(
            select(LicensePlate).where(LicensePlate.is_blacklisted == True)
        )
        blacklisted_count = len(blacklisted_plates.scalars().all())
        
        # Get recent detections count (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_detections = await db.execute(
            select(LicensePlateDetection).where(
                LicensePlateDetection.detected_at >= yesterday
            )
        )
        recent_count = len(recent_detections.scalars().all())
        
        return PlateStatsResponse(
            total_plates=total_count,
            authorized_plates=authorized_count,
            blacklisted_plates=blacklisted_count,
            recent_detections=recent_count,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error fetching plate statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch plate statistics"
        )

@router.get("/detections/recent", response_model=List[PlateDetectionResponse])
async def get_recent_detections(
    limit: int = Query(50, ge=1, le=500),
    hours: int = Query(24, ge=1, le=168),  # Max 1 week
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get recent license plate detections.
    
    Args:
        limit: Maximum number of detections to return
        hours: Number of hours to look back
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List[PlateDetectionResponse]: Recent detections
    """
    try:
        since_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = select(LicensePlateDetection).where(
            LicensePlateDetection.detected_at >= since_time
        ).order_by(LicensePlateDetection.detected_at.desc()).limit(limit)
        
        result = await db.execute(query)
        detections = result.scalars().all()
        
        return [PlateDetectionResponse.from_orm(detection) for detection in detections]
        
    except Exception as e:
        logger.error(f"Error fetching recent detections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch recent detections"
        )
