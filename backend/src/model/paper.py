from sqlalchemy import Boolean, ForeignKey, String, text, Enum as SQLAlchemyEnum, UniqueConstraint
from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database.db import Base, TimestampMixin
from ..lib.enum import PaperSourceEnum


class Paper(Base, TimestampMixin):
    """SQLAlchemy model for user Papers information."""

    __tablename__ = "paper"
    __table_args__ = (
        UniqueConstraint("user_id", "arxiv_id", name="uq_paper_user_arxiv"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    abstract: Mapped[str] = mapped_column(String, nullable=False)
    authors: Mapped[str] = mapped_column(String(512), nullable=False)
    arxiv_id: Mapped[str] = mapped_column(String(50), nullable=True)
    pdf_url: Mapped[str] = mapped_column(String, nullable=True)
    paper_url: Mapped[str | None] = mapped_column(String, nullable=True)
    github_url: Mapped[str | None] = mapped_column(String, nullable=True)
    paper_source: Mapped[str | None] = mapped_column(
        SQLAlchemyEnum(PaperSourceEnum, native_enum=False, length=50),
        nullable=False,
        server_default=PaperSourceEnum.ARXIV.value.upper(),
        default=PaperSourceEnum.ARXIV.value.upper(),
    )
    topics: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    published_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String, nullable=True)
    institution: Mapped[str | None] = mapped_column(String(255), nullable=True)
    date_published: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ingested: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false"), default=False
    )
    paper_summary: Mapped[str | None] = mapped_column(String, nullable=True)
    keywords: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    if TYPE_CHECKING:
        from .user import User  # pragma: no cover
        from .usability import Usability  # pragma: no cover
        from .chat_session import Session  # pragma: no cover
    user: Mapped["User"] = relationship("User", back_populates="papers")
    usabilities: Mapped[list["Usability"]] = relationship(
        "Usability", back_populates="paper", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="paper", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Paper(id={self.id}, title={self.title}, arxiv_id={self.arxiv_id})"
