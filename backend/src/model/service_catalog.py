from sqlalchemy import String, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column

from ..database.db import Base, TimestampMixin
from ..lib.enum import ServiceType


class ServiceCatalog(Base, TimestampMixin):
    """
    Service Catalog table where admins define which services users can add API keys for.

    The slug field is used as the key in UserSettings.api_keys dictionary.
    When users add API keys, they select from available services and the key is stored
    with the service slug as the identifier.

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

    __tablename__ = "service_catalog"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    service_type: Mapped[ServiceType] = mapped_column(
        SQLAlchemyEnum(ServiceType, native_enum=False, length=50),
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    def __repr__(self) -> str:
        return f"ServiceCatalog(id={self.id}, name={self.name}, slug={self.slug}, type={self.service_type})"

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "service_type": self.service_type.value,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
