from sqlalchemy import ForeignKey, String
from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database.db import Base, TimestampMixin


class Profile(Base, TimestampMixin):
    """SQLAlchemy model for user profile information."""

    __tablename__ = "profile"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"), nullable=False, index=True
    )
    phone: Mapped[str | None] = mapped_column(String(13), nullable=True)
    avatar: Mapped[str | None] = mapped_column(String, nullable=True)
    bio: Mapped[str | None] = mapped_column(String(255), nullable=True)
    topic_preferences: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    
    if TYPE_CHECKING:
        from .user import User  # pragma: no cover

    user: Mapped["User"] = relationship("User", back_populates="profile")

    def __repr__(self) -> str:
        return f"Profile(id={self.id}, user_id={self.user_id}, avatar={self.avatar}, bio={self.bio})"