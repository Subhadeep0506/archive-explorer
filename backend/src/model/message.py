from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String, Float, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database.db import Base, TimestampMixin


class Message(Base, TimestampMixin):
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("session.id"), nullable=False, index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id"), nullable=True, index=True
    )
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    parent_message_id: Mapped[int | None] = mapped_column(
        ForeignKey("message.id"), nullable=True, index=True
    )
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    liked: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=None)
    feedback: Mapped[str | None] = mapped_column(
        String(1024), nullable=True, default=""
    )
    stars: Mapped[int | None] = mapped_column(nullable=True, default=0)

    if TYPE_CHECKING:
        from .chat_session import Session  # pragma: no cover
        from .source import Source  # pragma: no cover

    session: Mapped["Session"] = relationship("Session", back_populates="messages")
    parent: Mapped["Message"] = relationship(
        "Message", remote_side=[id], backref="children"
    )
    sources: Mapped[list["Source"]] = relationship(
        "Source", back_populates="message", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Message(id={self.id}, session_id={self.session_id}, role={self.role})"
