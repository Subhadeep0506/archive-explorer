"""
Admin controller for managing users and service catalog.
Simple authentication with hardcoded admin:admin credentials.
"""

from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.model import User, ServiceCatalog
from src.lib.enum import ServiceType


# Simple admin credentials (hardcoded for now)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"


class AdminController:
    """Controller for admin operations."""

    @staticmethod
    def verify_admin_credentials(username: str, password: str) -> bool:
        """Verify admin credentials."""
        return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

    @staticmethod
    async def get_all_users(session: AsyncSession) -> list[User]:
        """Get all users."""
        result = await session.execute(select(User).order_by(User.created_at.desc()))
        return result.scalars().all()

    @staticmethod
    async def get_all_services(session: AsyncSession) -> list[ServiceCatalog]:
        """Get all services from catalog."""
        result = await session.execute(
            select(ServiceCatalog).order_by(
                ServiceCatalog.service_type, ServiceCatalog.name
            )
        )
        return result.scalars().all()

    @staticmethod
    async def get_service_by_id(
        session: AsyncSession, service_id: int
    ) -> Optional[ServiceCatalog]:
        """Get service by ID."""
        return await session.get(ServiceCatalog, service_id)

    @staticmethod
    async def create_service(
        session: AsyncSession,
        name: str,
        slug: str,
        service_type: ServiceType,
        description: Optional[str] = None,
        is_active: bool = True,
    ) -> ServiceCatalog:
        """Create a new service in the catalog."""
        service = ServiceCatalog(
            name=name,
            slug=slug,
            service_type=service_type,
            description=description,
            is_active=is_active,
        )
        session.add(service)
        await session.commit()
        await session.refresh(service)
        return service

    @staticmethod
    async def delete_service(session: AsyncSession, service_id: int) -> bool:
        """Delete a service from the catalog."""
        service = await session.get(ServiceCatalog, service_id)
        if service:
            await session.delete(service)
            await session.commit()
            return True
        return False

    @staticmethod
    async def toggle_service_status(
        session: AsyncSession, service_id: int
    ) -> Optional[ServiceCatalog]:
        """Toggle service active status."""
        service = await session.get(ServiceCatalog, service_id)
        if service:
            service.is_active = not service.is_active
            await session.commit()
            await session.refresh(service)
            return service
        return None

    @staticmethod
    async def get_user_count(session: AsyncSession) -> int:
        """Get total user count."""
        result = await session.execute(select(User))
        return len(result.scalars().all())

    @staticmethod
    async def get_service_count(session: AsyncSession) -> int:
        """Get total service count."""
        result = await session.execute(select(ServiceCatalog))
        return len(result.scalars().all())
