from pydantic import BaseModel, field_validator
from typing import Optional

from ..lib.categories import VALID_CATEGORY_CODES


class ProfileBase(BaseModel):
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    topic_preferences: Optional[str] = None

    @field_validator("topic_preferences")
    @classmethod
    def validate_topic_preferences(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == "":
            return None
        tags = [t.strip() for t in v.split(",") if t.strip()]
        invalid = [t for t in tags if t not in VALID_CATEGORY_CODES]
        if invalid:
            raise ValueError(
                f"Invalid arXiv categories: {', '.join(invalid)}. "
                f"Must be valid CS/stat/eess categories (e.g. cs.AI, stat.ML)."
            )
        return ",".join(tags)


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
