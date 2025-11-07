from typing import Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

# Enums
class CameraStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ERROR = "error"

# Camera Schemas
class CameraBase(BaseModel):
    """
    Base camera schema (shared fields for create/update/response).
    Mirrors the fields used by your SQLAlchemy model.
    """
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    location: Optional[str] = Field(None, max_length=200)
    stream_url: Optional[str] = Field(None, max_length=500)
    stream_type: str = Field("rtsp", max_length=20)
    fps: int = Field(25, ge=1, le=60)
    resolution_width: int = Field(1920, ge=320)
    resolution_height: int = Field(1080, ge=240)
    status: CameraStatus = Field(CameraStatus.INACTIVE)
    is_enabled: bool = Field(True)
    roi_x: int = Field(0, ge=0)
    roi_y: int = Field(0, ge=0)
    roi_width: int = Field(1920, ge=320)
    roi_height: int = Field(1080, ge=240)

class CameraCreate(CameraBase):
    pass

class CameraUpdate(BaseModel):
    """Schema used for partial updates to a camera."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    location: Optional[str] = Field(None, max_length=200)
    stream_url: Optional[str] = Field(None, max_length=500)
    stream_type: Optional[str] = Field(None, max_length=20)
    fps: Optional[int] = Field(None, ge=1, le=60)
    resolution_width: Optional[int] = Field(None, ge=320)
    resolution_height: Optional[int] = Field(None, ge=240)
    status: Optional[CameraStatus] = None
    is_enabled: Optional[bool] = None
    roi_x: Optional[int] = Field(None, ge=0)
    roi_y: Optional[int] = Field(None, ge=0)
    roi_width: Optional[int] = Field(None, ge=320)
    roi_height: Optional[int] = Field(None, ge=240)

class CameraResponse(CameraBase):
    """Response schema returned by endpoints (ORM -> response)."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None

    model_config = {"from_attributes": True}

class CameraStatsResponse(BaseModel):
    total_cameras: int
    active_cameras: int
    enabled_cameras: int
    status_counts: int
    timestamp: datetime
