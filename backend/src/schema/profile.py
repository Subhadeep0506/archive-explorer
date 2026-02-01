from pydantic import BaseModel
from typing import Optional


class ProfileBase(BaseModel):
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    topic_preferences: Optional[str] = None


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(ProfileBase):
    pass


class ProfileResponse(BaseModel):
    id: int
    user_id: int
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    topic_preferences: Optional[str] = None

    class Config:
        from_attributes = True
