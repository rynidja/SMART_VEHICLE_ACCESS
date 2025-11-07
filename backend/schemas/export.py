from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Export Schemas
class ExportRequest(BaseModel):
    """Schema for data export requests."""
    format: str = Field(..., pattern=r'^(csv|xlsx|json)$')
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
