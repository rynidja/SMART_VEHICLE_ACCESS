from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

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
