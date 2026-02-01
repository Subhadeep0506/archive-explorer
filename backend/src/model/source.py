from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Text, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database.db import Base, TimestampMixin


class Source(Base, TimestampMixin):
    __tablename__ = "source"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        ForeignKey("message.id"), nullable=False, index=True
    )
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    if TYPE_CHECKING:
        from .message import Message  # pragma: no cover

    message: Mapped["Message"] = relationship("Message", back_populates="sources")

    def __repr__(self) -> str:
        return f"Source(id={self.id}, message_id={self.message_id}, source_url={self.source_url})"
