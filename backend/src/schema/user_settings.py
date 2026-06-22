"""
Schema definitions for user settings.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ApiKeyItem(BaseModel):
    """API key item with service information."""

    id: int = Field(..., description="Service catalog ID")
    slug: str = Field(..., description="Service slug (e.g., 'tavily', 'groq')")
    name: str = Field(..., description="Service name (e.g., 'Tavily', 'Groq')")
    api_key: str = Field(..., description="The API key value")


class ServiceCatalogResponse(BaseModel):
    """Schema for service catalog response."""

    id: int
    name: str
    slug: str
    service_type: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResourceCatalogResponse(BaseModel):
    """Schema for resource catalog response."""

    id: int
    name: str
    slug: str
    service_id: int
    service_slug: Optional[str] = None
    service_name: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserSettingsBase(BaseModel):
    """Base schema for user settings."""

    location: Optional[str] = Field(None, max_length=100, description="User location")
    custom_summary_instructions: Optional[str] = Field(
        None, description="Custom instructions for paper summaries"
    )
    usability_analysis_instructions: Optional[str] = Field(
        None, description="Custom instructions for usability analysis"
    )
    summary_model: Optional[str] = Field(
        None, description="Selected model for paper summary generation"
    )
    usability_model: Optional[str] = Field(
        None, description="Selected model for usability analysis"
    )


class UserSettingsCreate(UserSettingsBase):
    """Schema for creating user settings."""

    api_keys_encrypted: Optional[list[ApiKeyItem]] = Field(
        None, description="List of encrypted API keys"
    )


class UserSettingsUpdate(BaseModel):
    """Schema for updating user settings. All fields are optional."""

    location: Optional[str] = Field(None, max_length=100, description="User location")
    custom_summary_instructions: Optional[str] = Field(
        None, description="Custom instructions for paper summaries"
    )
    usability_analysis_instructions: Optional[str] = Field(
        None, description="Custom instructions for usability analysis"
    )
    summary_model: Optional[str] = Field(
        None, description="Selected model for paper summary generation"
    )
    usability_model: Optional[str] = Field(
        None, description="Selected model for usability analysis"
    )
    api_keys_encrypted: Optional[list[ApiKeyItem]] = Field(
        None, description="List of encrypted API keys"
    )


class UserSettingsResponse(UserSettingsBase):
    """Schema for user settings response (without decrypted API keys)."""

    id: int
    user_id: int
    api_keys_encrypted: Optional[list[dict]] = Field(
        None, description="List of API key info (keys are encrypted)"
    )

    class Config:
        from_attributes = True


class UserSettingsWithApiKeys(UserSettingsResponse):
    """Schema for user settings with decrypted API keys (for internal use)."""

    api_keys: Optional[list[ApiKeyItem]] = Field(None, description="Decrypted API keys")

    class Config:
        from_attributes = True
