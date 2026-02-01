from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database.db import Base, TimestampMixin


class UserSettings(Base, TimestampMixin):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"), nullable=False, index=True
    )
    language_preference: Mapped[str | None] = mapped_column(
        String(8), nullable=True, server_default="en"
    )
    dark_mode_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    custom_instructions: Mapped[str | None] = mapped_column(String, nullable=True)

    if TYPE_CHECKING:
        from .user import User  # pragma: no cover

    user: Mapped["User"] = relationship("User", back_populates="user_settings")

    def __repr__(self) -> str:
        return f"UserSettings(id={self.id}, user_id={self.user_id}, language={self.language_preference})"