from fastapi import APIRouter, UploadFile, File, Depends
from ..controller.profile import (
    get_profile,
    create_profile,
    update_profile,
    upload_avatar,
)
from ..schema.profile import ProfileCreate, ProfileUpdate, ProfileResponse
from ..lib.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=ProfileResponse)
async def read_profile(user_id: int = Depends(get_current_user)):
    """Get current user's profile"""
    return await get_profile(user_id)


@router.post("/", response_model=ProfileResponse)
async def create_user_profile(
    profile_data: ProfileCreate, user_id: int = Depends(get_current_user)
):
    """Create user profile"""
    return await create_profile(user_id, profile_data)


@router.put("/", response_model=ProfileResponse)
async def update_user_profile(
    profile_data: ProfileUpdate, user_id: int = Depends(get_current_user)
):
    """Update user profile"""
    return await update_profile(user_id, profile_data)


@router.post("/avatar", response_model=ProfileResponse)
async def upload_user_avatar(
    file: UploadFile = File(...), user_id: int = Depends(get_current_user)
):
    """Upload user avatar"""
    return await upload_avatar(user_id, file)
