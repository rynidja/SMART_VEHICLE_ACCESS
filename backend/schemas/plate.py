# Pydantic schemas for API request/response models
# Defines data validation and serialization for all API endpoints

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"

class PlateStatus(str, Enum):
    AUTHORIZED = "authorized"
    DENIED = "denied"
    UNKNOWN = "unknown"
    PENDING = "pending"

class CameraStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ERROR = "error"

# User Schemas
class UserBase(BaseModel):
    """Base user schema with common fields."""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    role: UserRole = UserRole.VIEWER
    is_active: bool = True

class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8, max_length=100)

class UserUpdate(BaseModel):
    """Schema for updating user information."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = Field(None, regex=r'^[^@]+@[^@]+\.[^@]+$')
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)

class UserResponse(UserBase):
    """Schema for user response data."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True

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
    created_by: Optional[int]
    
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
    detection_confidence: float = Field(..., ge=0.0, le=1.0)
    ocr_confidence: float = Field(..., ge=0.0, le=1.0)
    overall_confidence: float = Field(..., ge=0.0, le=1.0)
    status: PlateStatus = PlateStatus.UNKNOWN
    decision_reason: Optional[str] = Field(None, max_length=200)
    thumbnail_path: Optional[str] = None
    full_image_path: Optional[str] = None
    bbox_x: Optional[int] = None
    bbox_y: Optional[int] = None
    bbox_width: Optional[int] = None
    bbox_height: Optional[int] = None
    processing_time_ms: Optional[int] = None
    frame_number: Optional[int] = None

class PlateDetectionCreate(PlateDetectionBase):
    """Schema for creating a new detection record."""
    camera_id: int

class PlateDetectionResponse(PlateDetectionBase):
    """Schema for detection response data."""
    id: int
    plate_hash: Optional[str]
    camera_id: int
    plate_id: Optional[int]
    detected_at: datetime
    
    class Config:
        from_attributes = True

# Camera Schemas
class CameraBase(BaseModel):
    """Base camera schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=200)
    stream_url: Optional[str] = Field(None, max_length=500)
    stream_type: str = Field(default="rtsp", max_length=20)
    fps: int = Field(default=25, ge=1, le=60)
    resolution_width: int = Field(default=1920, ge=320)
    resolution_height: int = Field(default=1080, ge=240)
    status: CameraStatus = CameraStatus.INACTIVE
    is_enabled: bool = True
    roi_x: int = Field(default=0, ge=0)
    roi_y: int = Field(default=0, ge=0)
    roi_width: int = Field(default=1920, ge=320)
    roi_height: int = Field(default=1080, ge=240)

class CameraCreate(CameraBase):
    """Schema for creating a new camera."""
    pass

class CameraUpdate(BaseModel):
    """Schema for updating camera information."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
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
    """Schema for camera response data."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    last_seen: Optional[datetime]
    
    class Config:
        from_attributes = True

# Authentication Schemas
class Token(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    """Schema for token data."""
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None

class LoginRequest(BaseModel):
    """Schema for login request."""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

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

# Audit Log Schemas
class AuditLogBase(BaseModel):
    """Base audit log schema."""
    action: str = Field(..., max_length=100)
    resource_type: Optional[str] = Field(None, max_length=50)
    resource_id: Optional[int] = None
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = Field(None, max_length=500)
    endpoint: Optional[str] = Field(None, max_length=200)
    details: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None

class AuditLogResponse(AuditLogBase):
    """Schema for audit log response data."""
    id: int
    user_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Error Schemas
class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ValidationError(BaseModel):
    """Schema for validation errors."""
    field: str
    message: str
    value: Any

# File Upload Schemas
class FileUploadResponse(BaseModel):
    """Schema for file upload response."""
    filename: str
    file_path: str
    file_size: int
    content_type: str
    uploaded_at: datetime

# Export Schemas
class ExportRequest(BaseModel):
    """Schema for data export requests."""
    format: str = Field(..., regex=r'^(csv|xlsx|json)$')
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    camera_ids: Optional[List[int]] = None
    plate_status: Optional[List[PlateStatus]] = None

class ExportResponse(BaseModel):
    """Schema for export response."""
    export_id: str
    status: str
    download_url: Optional[str] = None
    created_at: datetime
    expires_at: datetime
