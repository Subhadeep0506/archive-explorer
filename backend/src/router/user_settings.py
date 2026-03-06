"""
Router for user settings endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.db import session_pool
from src.controller.user_settings import UserSettingsController
from src.schema.user_settings import (
    UserSettingsResponse,
    UserSettingsUpdate,
    ServiceCatalogResponse,
)
from src.lib.auth import get_current_user
from src.model import ServiceCatalog

router = APIRouter()


async def get_session():
    """Dependency to get database session."""
    async with session_pool() as session:
        yield session


@router.get("/", response_model=UserSettingsResponse)
async def get_user_settings(
    user_id: int = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get current user's settings.
    Creates default settings if they don't exist.
    """
    settings = await UserSettingsController.get_or_create_user_settings(
        session, user_id
    )

    # Return settings with encrypted API keys (never send decrypted keys to frontend)
    response_data = {
        "id": settings.id,
        "user_id": settings.user_id,
        "location": settings.location,
        "custom_summary_instructions": settings.custom_summary_instructions,
        "usability_analysis_instructions": settings.usability_analysis_instructions,
        "api_keys_encrypted": settings.api_keys_encrypted,  # Return encrypted keys
    }

    return response_data


@router.put("/", response_model=UserSettingsResponse)
async def update_user_settings(
    settings_data: UserSettingsUpdate,
    user_id: int = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Update current user's settings.
    All fields are optional - only provided fields will be updated.
    """
    settings = await UserSettingsController.update_user_settings(
        session, user_id, settings_data
    )

    # Return settings with encrypted API keys (never send decrypted keys to frontend)
    response_data = {
        "id": settings.id,
        "user_id": settings.user_id,
        "location": settings.location,
        "custom_summary_instructions": settings.custom_summary_instructions,
        "usability_analysis_instructions": settings.usability_analysis_instructions,
        "api_keys_encrypted": settings.api_keys_encrypted,  # Return encrypted keys
    }

    return response_data


@router.get("/services", response_model=list[ServiceCatalogResponse])
async def get_services(
    user_id: int = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get available services from the catalog for users to add API keys.
    Only returns active services.
    """
    result = await session.execute(
        select(ServiceCatalog)
        .where(ServiceCatalog.is_active == True)
        .order_by(ServiceCatalog.service_type, ServiceCatalog.name)
    )
    services = result.scalars().all()
    return services
