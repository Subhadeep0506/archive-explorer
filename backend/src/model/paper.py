from sqlalchemy import ForeignKey, String
from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database.db import Base, TimestampMixin


class Paper(Base, TimestampMixin):
    """SQLAlchemy model for user Papers information."""

    __tablename__ = "paper"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    abstract: Mapped[str] = mapped_column(String, nullable=False)
    authors: Mapped[str] = mapped_column(String(512), nullable=False)
    arxiv_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    pdf_url: Mapped[str] = mapped_column(String, nullable=False)
    paper_url: Mapped[str | None] = mapped_column(String, nullable=True)
    github_url: Mapped[str | None] = mapped_column(String, nullable=True)
    topics: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    published_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String, nullable=True)
    institution: Mapped[str | None] = mapped_column(String(255), nullable=True)
    date_published: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    if TYPE_CHECKING:
        from .user import User  # pragma: no cover
    user: Mapped["User"] = relationship("User", back_populates="papers")

    def __repr__(self) -> str:
        return f"Paper(id={self.id}, title={self.title}, arxiv_id={self.arxiv_id})"