from sqlalchemy import Boolean, ForeignKey, String, Float, JSON, text
from typing import TYPE_CHECKING, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database.db import Base, TimestampMixin
from .paper import Paper


class Usability(Base, TimestampMixin):
    """SQLAlchemy model for user Paper Usability information."""

    __tablename__ = "usability"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"), nullable=False, index=True
    )
    paper_id: Mapped[int] = mapped_column(
        ForeignKey("paper.id"), nullable=False, index=True
    )
    domain_applicability: Mapped[dict] = mapped_column(JSON, nullable=False)
    reproducibility_score: Mapped[dict] = mapped_column(JSON, nullable=False)
    new_tech_applicability: Mapped[dict] = mapped_column(
        JSON, nullable=False, server_default=text("'{}'")
    )
    impact_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    if TYPE_CHECKING:
        from .user import User  # pragma: no cover
    user: Mapped["User"] = relationship("User", back_populates="usabilities")
    paper: Mapped["Paper"] = relationship("Paper", back_populates="usabilities")

    def __repr__(self) -> str:
        return (
            f"Usability(id={self.id}, user_id={self.user_id}, paper_id={self.paper_id})"
        )
