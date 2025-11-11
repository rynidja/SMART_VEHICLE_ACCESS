from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
from backend.schemas.auth import UserResponse

# Enums
class PlateStatus(str, Enum):
    AUTHORIZED = "authorized"
    DENIED = "denied"
    UNKNOWN = "unknown"
    PENDING = "pending"

    @classmethod
    def from_flags(cls, is_authorised: bool, is_backlisted: bool) -> "PlateStatus":
        if is_backlisted:
            return cls.DENIED
        if is_authorised:
            return cls.AUTHORIZED
        return cls.UNKNOWN

# License Plate Schemas
class PlateBase(BaseModel):
    """Base license plate schema."""
    plate_text: str = Field(..., min_length=1, max_length=20)
    country_code: str = Field(default="DZ", max_length=3)
    plate_type: Optional[str] = Field(None, max_length=20)
    is_authorized: bool = True
    is_blacklisted: bool = False
    owner_name: Optional[str] = Field(None, max_length=100)
    owner_contact: Optional[str] = Field(None, max_length=100)
    vehicle_info: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

class PlateCreate(PlateBase):
    """Schema for creating a new license plate entry."""
    pass

class PlateUpdate(BaseModel):
    """Schema for updating license plate information."""
    plate_text: Optional[str] = Field(None, min_length=1, max_length=20)
    country_code: Optional[str] = Field(None, max_length=3)
    plate_type: Optional[str] = Field(None, max_length=20)
    is_authorized: Optional[bool] = None
    is_blacklisted: Optional[bool] = None
    owner_name: Optional[str] = Field(None, max_length=100)
    owner_contact: Optional[str] = Field(None, max_length=100)
    vehicle_info: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

class PlateResponse(PlateBase):
    """Schema for license plate response data."""
    id: int
    plate_hash: str
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    
    class Config:
        from_attributes = True

class PlateSearchRequest(BaseModel):
    """Schema for license plate search requests."""
    plate_text: Optional[str] = None
    owner_name: Optional[str] = None
    country_code: Optional[str] = None
    plate_type: Optional[str] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)

class PlateStatsResponse(BaseModel):
    """Schema for license plate statistics."""
    total_plates: int
    authorized_plates: int
    blacklisted_plates: int
    recent_detections: int
    timestamp: datetime

# License Plate Detection Schemas
class PlateDetectionBase(BaseModel):
    """Base license plate detection schema."""
    detected_plate_text: str = Field(..., min_length=1, max_length=20)
    overall_confidence: float = Field(..., ge=0.0, le=1.0)
    status: PlateStatus = PlateStatus.UNKNOWN
    thumbnail_path: Optional[str] = None
    processing_time_ms: Optional[int] = None

class PlateDetectionResponse(PlateDetectionBase):
    """Schema for detection response data."""
    id: int
    plate_hash: Optional[str]
    camera_id: int
    plate_id: Optional[int]
    detected_at: datetime
    
    class Config:
        from_attributes = True
