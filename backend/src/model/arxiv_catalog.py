from sqlalchemy import Boolean, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column
from ..database.db import Base, TimestampMixin


class ArxivCatalog(Base, TimestampMixin):
    """Catalog of ArXiv papers harvested via OAI-PMH. Used for feed queries and recommendation indexing."""

    __tablename__ = "arxiv_catalog"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    arxiv_id: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    abstract: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    categories: Mapped[str | None] = mapped_column(String(256), nullable=True)
    primary_category: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )
    published_date: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )
    updated_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    pdf_url: Mapped[str | None] = mapped_column(String, nullable=True)
    paper_url: Mapped[str | None] = mapped_column(String, nullable=True)
    indexed_in_qdrant: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false"), default=False
    )

    def __repr__(self) -> str:
        return f"ArxivCatalog(id={self.id}, arxiv_id={self.arxiv_id}, title={self.title[:50]})"
