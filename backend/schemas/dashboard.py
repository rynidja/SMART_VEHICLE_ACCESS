from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime

# Dashboard Schemas
class DashboardStats(BaseModel):
    """Schema for dashboard statistics."""
    total_cameras: int
    active_cameras: int
    total_plates: int
    authorized_plates: int
    blacklisted_plates: int
    detections_today: int
    detections_this_hour: int
    system_status: str
    last_detection: Optional[datetime]
    timestamp: datetime

class SystemHealth(BaseModel):
    """Schema for system health status."""
    status: str
    database: bool
    redis: bool
    cameras: Dict[str, bool]
    processing_queue: int
    memory_usage: float
    cpu_usage: float
    disk_usage: float
    timestamp: datetime
