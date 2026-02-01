from pydantic import BaseModel
from typing import Optional
from datetime import date


class SessionBase(BaseModel):
    started_at: date
    ended_at: Optional[date] = None
    device_type: Optional[str] = None


class SessionCreate(SessionBase):
    user_id: int


class SessionUpdate(BaseModel):
    started_at: Optional[date] = None
    ended_at: Optional[date] = None
    device_type: Optional[str] = None


class SessionResponse(SessionBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
