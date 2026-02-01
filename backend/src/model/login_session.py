from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database.db import Base, TimestampMixin


class LoginSession(Base, TimestampMixin):
    """SQLAlchemy model for tracking user login sessions with JWT tokens."""

    __tablename__ = "login_session"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"), nullable=False, index=True
    )
    login_method: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'google', 'password', etc.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    device_info: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(
        String(45), nullable=True
    )  # IPv6 support
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(nullable=True)
    logout_at: Mapped[datetime | None] = mapped_column(nullable=True)

    if TYPE_CHECKING:
        from .user import User  # pragma: no cover

    user: Mapped["User"] = relationship("User", back_populates="login_sessions")

    def __repr__(self) -> str:
        return f"LoginSession(id={self.id}, user_id={self.user_id}, login_method={self.login_method}, is_active={self.is_active})"