from datetime import date
from typing import TYPE_CHECKING, Optional, Union
from sqlalchemy import CheckConstraint, String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database.db import Base, TimestampMixin
from ..lib.enum import UserRole

if TYPE_CHECKING:
    from .profile import Profile
    from .user_settings import UserSettings
    from .login_session import LoginSession
    from .chat_session import Session
    from .paper import Paper


class User(Base, TimestampMixin):
    """SQLAlchemy model for the users table."""

    __tablename__ = "user"
    __table_args__ = (
        CheckConstraint(
            "email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$'",
            name="ck_users_email_format",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    google_id: Mapped[str | None] = mapped_column(
        String(50), nullable=True, unique=True
    )
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole), nullable=False, default=UserRole.USER
    )

    # relationships
    profile: Mapped["Profile"] = relationship(
        "Profile", uselist=False, back_populates="user", cascade="all, delete-orphan"
    )
    user_settings: Mapped["UserSettings"] = relationship(
        "UserSettings",
        uselist=False,
        back_populates="user",
        cascade="all, delete-orphan",
    )
    login_sessions: Mapped[list["LoginSession"]] = relationship(
        "LoginSession", back_populates="user", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
    papers: Mapped[list["Paper"]] = relationship(
        "Paper", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, full_name={self.full_name}, email={self.email})"
