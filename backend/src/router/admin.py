"""
Admin router for managing users and service catalog via web interface.
Uses Jinja2 templates for server-side rendering.
"""

from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import session_pool
from src.controller.admin import AdminController
from src.lib.enum import ServiceType
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# Dependency to get database session
async def get_session():
    async with session_pool() as session:
        yield session


# Simple session management (in-memory for now)
admin_sessions = set()


def is_admin_authenticated(request: Request) -> bool:
    """Check if admin is authenticated via session cookie."""
    session_id = request.cookies.get("admin_session")
    return session_id in admin_sessions


def require_admin_auth(request: Request):
    """Dependency to require admin authentication."""
    if not is_admin_authenticated(request):
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/admin/login"}
        )


@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Render admin login page."""
    # If already authenticated, redirect to dashboard
    if is_admin_authenticated(request):
        return RedirectResponse(url="/admin/dashboard", status_code=303)

    return templates.TemplateResponse(
        "admin/login.html", {"request": request, "error": None}
    )


@router.post("/login")
async def admin_login(
    request: Request, username: str = Form(...), password: str = Form(...)
):
    """Handle admin login."""
    if AdminController.verify_admin_credentials(username, password):
        # Create session
        import secrets

        session_id = secrets.token_urlsafe(32)
        admin_sessions.add(session_id)

        # Redirect to dashboard with session cookie
        response = RedirectResponse(url="/admin/dashboard", status_code=303)
        response.set_cookie(
            key="admin_session",
            value=session_id,
            httponly=True,
            max_age=3600 * 8,  # 8 hours
        )
        return response

    # Invalid credentials
    return templates.TemplateResponse(
        "admin/login.html",
        {"request": request, "error": "Invalid username or password"},
        status_code=401,
    )


@router.get("/logout")
async def admin_logout(request: Request):
    """Handle admin logout."""
    session_id = request.cookies.get("admin_session")
    if session_id in admin_sessions:
        admin_sessions.remove(session_id)

    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie("admin_session")
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request, session: AsyncSession = Depends(get_session)
):
    """Render admin dashboard."""
    require_admin_auth(request)

    # Get statistics
    user_count = await AdminController.get_user_count(session)
    service_count = await AdminController.get_service_count(session)
    users = await AdminController.get_all_users(session)

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "user_count": user_count,
            "service_count": service_count,
            "users": users[:10],  # Show last 10 users
        },
    )


@router.get("/services", response_class=HTMLResponse)
async def admin_services(
    request: Request, session: AsyncSession = Depends(get_session)
):
    """Render services management page."""
    require_admin_auth(request)

    services = await AdminController.get_all_services(session)

    return templates.TemplateResponse(
        "admin/services.html",
        {
            "request": request,
            "services": services,
            "service_types": [st for st in ServiceType],
        },
    )


@router.post("/services/add")
async def admin_add_service(
    request: Request,
    name: str = Form(...),
    slug: str = Form(...),
    service_type: str = Form(...),
    description: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_session),
):
    """Add a new service."""
    require_admin_auth(request)

    try:
        # Convert string to ServiceType enum
        service_type_enum = ServiceType(service_type)

        await AdminController.create_service(
            session=session,
            name=name,
            slug=slug,
            service_type=service_type_enum,
            description=description,
        )

        return RedirectResponse(url="/admin/services?success=added", status_code=303)
    except Exception as e:
        return RedirectResponse(url=f"/admin/services?error={str(e)}", status_code=303)


@router.post("/services/delete/{service_id}")
async def admin_delete_service(
    request: Request, service_id: int, session: AsyncSession = Depends(get_session)
):
    """Delete a service."""
    require_admin_auth(request)

    success = await AdminController.delete_service(session, service_id)

    if success:
        return RedirectResponse(url="/admin/services?success=deleted", status_code=303)
    else:
        return RedirectResponse(url="/admin/services?error=not_found", status_code=303)


@router.post("/services/toggle/{service_id}")
async def admin_toggle_service(
    request: Request, service_id: int, session: AsyncSession = Depends(get_session)
):
    """Toggle service active status."""
    require_admin_auth(request)

    service = await AdminController.toggle_service_status(session, service_id)

    if service:
        return RedirectResponse(url="/admin/services?success=toggled", status_code=303)
    else:
        return RedirectResponse(url="/admin/services?error=not_found", status_code=303)


@router.get("/users", response_class=HTMLResponse)
async def admin_users(request: Request, session: AsyncSession = Depends(get_session)):
    """Render users management page."""
    require_admin_auth(request)

    users = await AdminController.get_all_users(session)

    return templates.TemplateResponse(
        "admin/users.html", {"request": request, "users": users}
    )
