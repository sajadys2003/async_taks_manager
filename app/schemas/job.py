from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.enums import JobStatus

class JobCreate(BaseModel):
    payload: str

class JobResponse(BaseModel):
    id: int
    user_id: int
    status: JobStatus
    payload: Optional[str] = None
    time_created: datetime
    time_started: Optional[datetime] = None
    time_done: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class PaginatedJobResponse(BaseModel):
    data: List[JobResponse]
    next_cursor: Optional[int] = None
    fetched_at: datetime