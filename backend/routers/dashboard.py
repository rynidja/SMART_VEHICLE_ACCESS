# Dashboard API router
# Provides dashboard data, statistics, and system monitoring

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from backend.database import get_async_db
from backend.models.database import (
    Camera, LicensePlate, LicensePlateDetection, 
    CameraStatus, PlateStatus, AuditLog
)
from backend.core.security import verify_token
from backend.schemas.dashboard import (
    DashboardStats, SystemHealth, RecentDetectionResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get comprehensive dashboard statistics.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        DashboardStats: Dashboard statistics
    """
    try:
        # Get camera statistics
        total_cameras_result = await db.execute(select(func.count(Camera.id)))
        total_cameras = total_cameras_result.scalar()
        
        active_cameras_result = await db.execute(
            select(func.count(Camera.id)).where(Camera.status == CameraStatus.ACTIVE)
        )
        active_cameras = active_cameras_result.scalar()
        
        # Get license plate statistics
        total_plates_result = await db.execute(select(func.count(LicensePlate.id)))
        total_plates = total_plates_result.scalar()
        
        authorized_plates_result = await db.execute(
            select(func.count(LicensePlate.id)).where(LicensePlate.is_authorized == True)
        )
        authorized_plates = authorized_plates_result.scalar()
        
        blacklisted_plates_result = await db.execute(
            select(func.count(LicensePlate.id)).where(LicensePlate.is_blacklisted == True)
        )
        blacklisted_plates = blacklisted_plates_result.scalar()
        
        # Get detection statistics
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        detections_today_result = await db.execute(
            select(func.count(LicensePlateDetection.id)).where(
                LicensePlateDetection.detected_at >= today
            )
        )
        detections_today = detections_today_result.scalar()
        
        # Get detections in the last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        detections_this_hour_result = await db.execute(
            select(func.count(LicensePlateDetection.id)).where(
                LicensePlateDetection.detected_at >= one_hour_ago
            )
        )
        detections_this_hour = detections_this_hour_result.scalar()
        
        # Get last detection timestamp
        last_detection_result = await db.execute(
            select(LicensePlateDetection.detected_at)
            .order_by(LicensePlateDetection.detected_at.desc())
            .limit(1)
        )
        last_detection = last_detection_result.scalar()
        
        # Determine system status
        system_status = "healthy"
        if active_cameras == 0:
            system_status = "no_active_cameras"
        elif detections_this_hour == 0 and active_cameras > 0:
            system_status = "no_recent_detections"
        
        return DashboardStats(
            total_cameras=total_cameras,
            active_cameras=active_cameras,
            total_plates=total_plates,
            authorized_plates=authorized_plates,
            blacklisted_plates=blacklisted_plates,
            detections_today=detections_today,
            detections_this_hour=detections_this_hour,
            system_status=system_status,
            last_detection=last_detection,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard statistics"
        )

@router.get("/health", response_model=SystemHealth)
async def get_system_health(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get system health status.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        SystemHealth: System health information
    """
    try:
        # Check database connectivity
        database_healthy = True
        try:
            await db.execute(select(1))
        except Exception:
            database_healthy = False
        
        # Check Redis connectivity (placeholder)
        redis_healthy = True  # In real implementation, check Redis connection
        
        # Check camera statuses
        cameras_result = await db.execute(select(Camera))
        cameras = cameras_result.scalars().all()
        
        camera_statuses = {}
        for camera in cameras:
            camera_statuses[camera.name] = camera.status == CameraStatus.ACTIVE
        
        # Get processing queue size (placeholder)
        processing_queue_size = 0  # In real implementation, check actual queue
        
        # Get system resource usage (placeholder)
        memory_usage = 0.0  # In real implementation, get actual memory usage
        cpu_usage = 0.0      # In real implementation, get actual CPU usage
        disk_usage = 0.0     # In real implementation, get actual disk usage
        
        # Determine overall system status
        overall_status = "healthy"
        if not database_healthy:
            overall_status = "database_error"
        elif not redis_healthy:
            overall_status = "redis_error"
        elif not any(camera_statuses.values()):
            overall_status = "no_active_cameras"
        
        return SystemHealth(
            status=overall_status,
            database=database_healthy,
            redis=redis_healthy,
            cameras=camera_statuses,
            processing_queue=processing_queue_size,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            disk_usage=disk_usage,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error checking system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check system health"
        )

@router.get("/recent-detections", response_model=List[RecentDetectionResponse])
async def get_recent_detections(
    limit: int = 50,
    hours: int = 24,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get recent license plate detections for dashboard.
    
    Args:
        limit: Maximum number of detections to return
        hours: Number of hours to look back
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List[RecentDetectionResponse]: Recent detections
    """
    try:
        since_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Query recent detections with camera information
        query = (
            select(LicensePlateDetection, Camera.name.label("camera_name"))
            .join(Camera, LicensePlateDetection.camera_id == Camera.id)
            .where(LicensePlateDetection.detected_at >= since_time)
            .order_by(LicensePlateDetection.detected_at.desc())
            .limit(limit)
        )
        
        result = await db.execute(query)
        detections = result.all()
        
        # Convert to response format
        recent_detections = []
        for detection, camera_name in detections:
            recent_detections.append(RecentDetectionResponse(
                id=detection.id,
                detected_plate_text=detection.detected_plate_text,
                camera_name=camera_name,
                status=detection.status.value,
                confidence=detection.overall_confidence,
                detected_at=detection.detected_at,
                thumbnail_path=detection.thumbnail_path
            ))
        
        return recent_detections
        
    except Exception as e:
        logger.error(f"Error fetching recent detections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch recent detections"
        )

@router.get("/detection-trends")
async def get_detection_trends(
    days: int = 7,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get detection trends over time.
    
    Args:
        days: Number of days to analyze
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        dict: Detection trends data
    """
    try:
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Get daily detection counts
        daily_detections = []
        for i in range(days):
            date = since_date + timedelta(days=i)
            next_date = date + timedelta(days=1)
            
            result = await db.execute(
                select(func.count(LicensePlateDetection.id))
                .where(
                    and_(
                        LicensePlateDetection.detected_at >= date,
                        LicensePlateDetection.detected_at < next_date
                    )
                )
            )
            count = result.scalar()
            
            daily_detections.append({
                "date": date.strftime("%Y-%m-%d"),
                "count": count
            })
        
        # Get status breakdown
        status_breakdown = {}
        for status in PlateStatus:
            result = await db.execute(
                select(func.count(LicensePlateDetection.id))
                .where(
                    and_(
                        LicensePlateDetection.status == status,
                        LicensePlateDetection.detected_at >= since_date
                    )
                )
            )
            status_breakdown[status.value] = result.scalar()
        
        return {
            "daily_detections": daily_detections,
            "status_breakdown": status_breakdown,
            "total_detections": sum(daily["count"] for daily in daily_detections),
            "period_days": days,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error fetching detection trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch detection trends"
        )

@router.get("/camera-performance")
async def get_camera_performance(
    camera_id: Optional[int] = None,
    hours: int = 24,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get camera performance metrics.
    
    Args:
        camera_id: Specific camera ID (optional)
        hours: Number of hours to analyze
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        dict: Camera performance data
    """
    try:
        since_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Build query
        query = select(LicensePlateDetection).where(
            LicensePlateDetection.detected_at >= since_time
        )
        
        if camera_id:
            query = query.where(LicensePlateDetection.camera_id == camera_id)
        
        result = await db.execute(query)
        detections = result.scalars().all()
        
        if not detections:
            return {
                "total_detections": 0,
                "average_confidence": 0.0,
                "average_processing_time": 0.0,
                "success_rate": 0.0,
                "cameras": []
            }
        
        # Calculate metrics
        total_detections = len(detections)
        average_confidence = sum(d.overall_confidence for d in detections) / total_detections
        
        processing_times = [d.processing_time_ms for d in detections if d.processing_time_ms]
        average_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        successful_detections = sum(1 for d in detections if d.status in [PlateStatus.AUTHORIZED, PlateStatus.DENIED])
        success_rate = successful_detections / total_detections if total_detections > 0 else 0
        
        # Get camera-specific data
        camera_stats = {}
        for detection in detections:
            camera_id = detection.camera_id
            if camera_id not in camera_stats:
                camera_stats[camera_id] = {
                    "detections": 0,
                    "total_confidence": 0.0,
                    "successful_detections": 0
                }
            
            camera_stats[camera_id]["detections"] += 1
            camera_stats[camera_id]["total_confidence"] += detection.overall_confidence
            
            if detection.status in [PlateStatus.AUTHORIZED, PlateStatus.DENIED]:
                camera_stats[camera_id]["successful_detections"] += 1
        
        # Format camera statistics
        cameras = []
        for cam_id, stats in camera_stats.items():
            cameras.append({
                "camera_id": cam_id,
                "detections": stats["detections"],
                "average_confidence": stats["total_confidence"] / stats["detections"],
                "success_rate": stats["successful_detections"] / stats["detections"]
            })
        
        return {
            "total_detections": total_detections,
            "average_confidence": average_confidence,
            "average_processing_time": average_processing_time,
            "success_rate": success_rate,
            "cameras": cameras,
            "period_hours": hours,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error fetching camera performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch camera performance"
        )

@router.get("/alerts")
async def get_system_alerts(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get system alerts and notifications.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        dict: System alerts
    """
    try:
        alerts = []
        
        # Check for cameras that haven't been seen recently
        cameras_result = await db.execute(select(Camera))
        cameras = cameras_result.scalars().all()
        
        for camera in cameras:
            if camera.status == CameraStatus.ACTIVE:
                # Check if camera hasn't been seen in the last 5 minutes
                if camera.last_seen:
                    time_since_seen = datetime.utcnow() - camera.last_seen
                    if time_since_seen > timedelta(minutes=5):
                        alerts.append({
                            "type": "camera_offline",
                            "severity": "warning",
                            "message": f"Camera '{camera.name}' has been offline for {time_since_seen}",
                            "timestamp": datetime.utcnow()
                        })
        
        # Check for high error rates
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_detections_result = await db.execute(
            select(func.count(LicensePlateDetection.id))
            .where(LicensePlateDetection.detected_at >= one_hour_ago)
        )
        recent_detections = recent_detections_result.scalar()
        
        if recent_detections == 0 and len([c for c in cameras if c.status == CameraStatus.ACTIVE]) > 0:
            alerts.append({
                "type": "no_detections",
                "severity": "info",
                "message": "No license plate detections in the last hour",
                "timestamp": datetime.utcnow()
            })
        
        return {
            "alerts": alerts,
            "total_alerts": len(alerts),
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error fetching system alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch system alerts"
        )
