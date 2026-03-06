from pydantic import BaseModel, Field
from typing import Optional, Union, List
from datetime import datetime
from .source import SourceResponse


class MessageBase(BaseModel):
    session_id: int
    # Content can be either a single dict or list of dicts (for conversation pairs)
    content: Union[dict, list[dict]]
    parent_message_id: Optional[int] = None
    model_used: Optional[str] = None
    confidence_score: Optional[float] = None
    liked: Optional[bool] = None
    feedback: Optional[str] = ""
    stars: Optional[int] = 0
    generation_metadata: Optional[dict] = None


class MessageCreate(MessageBase):
    user_id: Optional[int] = None


class MessageUpdate(BaseModel):
    content: Optional[Union[dict, list[dict]]] = None
    liked: Optional[bool] = None
    feedback: Optional[str] = None
    stars: Optional[int] = None


class MessageResponse(MessageBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    sources: List[SourceResponse] = []

    class Config:
        from_attributes = True
