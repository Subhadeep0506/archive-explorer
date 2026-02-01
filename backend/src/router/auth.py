from fastapi import APIRouter, Request, Depends
from ..controller.auth import (
    initiate_google_login,
    handle_google_callback,
    logout_user,
    get_user_sessions,
    register_user,
    login_user,
    delete_user_account,
)
from ..schema.auth import RegisterRequest, LoginRequest
from ..lib.auth import get_current_user

router = APIRouter()


@router.post("/register")
async def register(register_data: RegisterRequest):
    """Register a new user"""
    return await register_user(register_data)


@router.post("/login")
async def login(login_data: LoginRequest, request: Request):
    """Login with email and password"""
    return await login_user(login_data, request)


@router.get("/google/login")
async def login_google():
    """Initiate Google OAuth2 login"""
    return await initiate_google_login()


@router.get("/google/callback")
async def auth_google_callback(code: str, state: str, request: Request):
    """Handle Google OAuth2 callback"""
    return await handle_google_callback(code, state, request)


@router.post("/logout")
async def logout(user_id: int = Depends(get_current_user)):
    """Logout current user from all sessions"""
    return await logout_user(user_id)


@router.post("/logout/{session_id}")
async def logout_session(session_id: int, user_id: int = Depends(get_current_user)):
    """Logout from specific session"""
    return await logout_user(user_id, session_id)


@router.get("/sessions")
async def get_sessions(user_id: int = Depends(get_current_user)):
    """Get user's login sessions"""
    return await get_user_sessions(user_id)


@router.delete("/account")
async def delete_account(user_id: int = Depends(get_current_user)):
    """Delete user account and all associated data"""
    return await delete_user_account(user_id)
