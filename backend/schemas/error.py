from pydantic import BaseModel, Field 
from typing import Optional, Any
from datetime import datetime

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
