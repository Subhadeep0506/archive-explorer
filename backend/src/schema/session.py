from pydantic import BaseModel
from typing import Optional
from datetime import date


class SessionBase(BaseModel):
    title: Optional[str] = "New Session"
    paper_id: Optional[int] = None
    started_at: date
    ended_at: Optional[date] = None
    device_type: Optional[str] = None


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    title: Optional[str] = None
    started_at: Optional[date] = None
    ended_at: Optional[date] = None
    device_type: Optional[str] = None


class SessionResponse(SessionBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
