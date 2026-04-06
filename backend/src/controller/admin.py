"""
Admin controller for managing users and service catalog.
Simple authentication with hardcoded admin:admin credentials.
"""

from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.model import User, ServiceCatalog, ResourceCatalog
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

    # ==================== Resource Catalog Methods ====================

    @staticmethod
    async def get_all_resources(session: AsyncSession) -> list[ResourceCatalog]:
        """Get all resources from catalog with service information."""
        result = await session.execute(
            select(ResourceCatalog)
            .options(selectinload(ResourceCatalog.service))
            .order_by(ResourceCatalog.service_id, ResourceCatalog.name)
        )
        return result.scalars().all()

    @staticmethod
    async def get_resources_by_service(
        session: AsyncSession, service_id: int
    ) -> list[ResourceCatalog]:
        """Get all resources for a specific service."""
        result = await session.execute(
            select(ResourceCatalog)
            .where(ResourceCatalog.service_id == service_id)
            .order_by(ResourceCatalog.name)
        )
        return result.scalars().all()

    @staticmethod
    async def get_resource_by_id(
        session: AsyncSession, resource_id: int
    ) -> Optional[ResourceCatalog]:
        """Get resource by ID."""
        result = await session.execute(
            select(ResourceCatalog)
            .options(selectinload(ResourceCatalog.service))
            .where(ResourceCatalog.id == resource_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_resource_by_slug(
        session: AsyncSession, slug: str
    ) -> Optional[ResourceCatalog]:
        """Get resource by slug."""
        result = await session.execute(
            select(ResourceCatalog)
            .options(selectinload(ResourceCatalog.service))
            .where(ResourceCatalog.slug == slug)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_resource(
        session: AsyncSession,
        name: str,
        slug: str,
        service_id: int,
        description: Optional[str] = None,
        is_active: bool = True,
    ) -> ResourceCatalog:
        """Create a new resource in the catalog."""
        resource = ResourceCatalog(
            name=name,
            slug=slug,
            service_id=service_id,
            description=description,
            is_active=is_active,
        )
        session.add(resource)
        await session.commit()
        await session.refresh(resource)
        return resource

    @staticmethod
    async def delete_resource(session: AsyncSession, resource_id: int) -> bool:
        """Delete a resource from the catalog."""
        resource = await session.get(ResourceCatalog, resource_id)
        if resource:
            await session.delete(resource)
            await session.commit()
            return True
        return False

    @staticmethod
    async def toggle_resource_status(
        session: AsyncSession, resource_id: int
    ) -> Optional[ResourceCatalog]:
        """Toggle resource active status."""
        resource = await session.get(ResourceCatalog, resource_id)
        if resource:
            resource.is_active = not resource.is_active
            await session.commit()
            await session.refresh(resource)
            return resource
        return None

    @staticmethod
    async def get_resource_count(session: AsyncSession) -> int:
        """Get total resource count."""
        result = await session.execute(select(ResourceCatalog))
        return len(result.scalars().all())
