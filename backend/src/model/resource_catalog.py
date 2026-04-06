from sqlalchemy import String, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship
from ..database.db import Base, TimestampMixin
from .service_catalog import ServiceCatalog


class ResourceCatalog(Base, TimestampMixin):
    """
    Resource Catalog table where admins define which resources users can add API keys for.

    The slug field is used as the key in UserSettings.api_keys dictionary.
    When users add API keys, they select from available resources and the key is stored
    with the resource slug as the identifier.

    Examples:
    - Tavily (web search) - slug: "tavily"
    - LangSearch (web search) - slug: "langsearch"
    - Firecrawl (web scrape) - slug: "firecrawl"
    - Groq (LLM) - slug: "groq"
    - OpenAI (LLM, embedding) - slug: "openai"
    - Cohere (LLM, embedding, rerank) - slug: "cohere"
    - Pinecone (vector store) - slug: "pinecone"
    - Gemini (LLM) - slug: "gemini"
    """

    __tablename__ = "resource_catalog"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=False)
    slug: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    service_id: Mapped[int] = mapped_column(
        ForeignKey("service_catalog.id"), nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    service: Mapped["ServiceCatalog"] = relationship("ServiceCatalog", back_populates="resources")

    def __repr__(self) -> str:
        return f"ResourceCatalog(id={self.id}, name={self.name}, slug={self.slug}, service_id={self.service_id})"

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "service_id": self.service_id,
            "service_slug": self.service.slug if self.service else None,
            "service_name": self.service.name if self.service else None,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
