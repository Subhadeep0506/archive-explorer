from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class SourceBase(BaseModel):
    source_text: Optional[str] = None
    source_type: Optional[str] = None
    source_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SourceCreate(SourceBase):
    message_id: int


class SourceResponse(SourceBase):
    id: int
    message_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
