from datetime import date
from typing import TYPE_CHECKING
from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database.db import Base, TimestampMixin
from .message import Message


class Session(Base, TimestampMixin):
    __tablename__ = "session"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(
        String(100), nullable=False, default="New Session"
    )
    started_at: Mapped[date] = mapped_column(Date, nullable=False)
    ended_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    device_type: Mapped[str | None] = mapped_column(String(20), nullable=True)

    if TYPE_CHECKING:
        from .user import User  # pragma: no cover

    user: Mapped["User"] = relationship("User", back_populates="sessions")
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Session(id={self.id}, user_id={self.user_id}, started_at={self.started_at})"