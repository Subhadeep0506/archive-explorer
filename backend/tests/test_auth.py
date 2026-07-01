import asyncio

from sqlalchemy import select

from src.database.db import session_pool
from src.model import Profile, User, UserSettings


def test_register_creates_user_profile_and_settings(client):
    payload = {
        "email": "new-user@example.com",
        "password": "Password123!",
        "full_name": "New User",
        "username": "new_user",
    }

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 200
    assert response.json()["email"] == payload["email"]

    async def _load_user_state():
        async with session_pool() as session:
            user = (
                await session.execute(select(User).where(User.email == payload["email"]))
            ).scalar_one()
            profile = (
                await session.execute(select(Profile).where(Profile.user_id == user.id))
            ).scalar_one_or_none()
            settings = (
                await session.execute(
                    select(UserSettings).where(UserSettings.user_id == user.id)
                )
            ).scalar_one_or_none()
            return user, profile, settings

    user, profile, settings = asyncio.run(_load_user_state())
    assert user.username == payload["username"]
    assert profile is not None
    assert settings is not None


def test_register_rejects_duplicate_email(client, create_user):
    create_user(email="duplicate@example.com", username="original_user")

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "Password123!",
            "full_name": "Another User",
            "username": "another_user",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_register_rejects_duplicate_username(client, create_user):
    create_user(email="existing@example.com", username="taken_name")

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@example.com",
            "password": "Password123!",
            "full_name": "Another User",
            "username": "taken_name",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Username already taken"


def test_login_refresh_logout_and_session_listing(client, create_user):
    user = create_user(
        email="login@example.com",
        username="login_user",
        password="Password123!",
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": user["email"], "password": user["password"]},
        headers={"user-agent": "pytest"},
    )

    assert login_response.status_code == 200
    login_payload = login_response.json()
    assert login_payload["token_type"] == "bearer"
    assert login_payload["user"]["email"] == user["email"]

    access_token = login_payload["access_token"]
    refresh_token = login_payload["refresh_token"]

    sessions_response = client.get(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert sessions_response.status_code == 200
    sessions = sessions_response.json()
    assert len(sessions) == 1
    assert sessions[0]["is_active"] is True

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 200
    refreshed_access_token = refresh_response.json()["access_token"]
    assert refreshed_access_token != access_token

    logout_response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {refreshed_access_token}"},
    )
    assert logout_response.status_code == 200
    assert logout_response.json()["message"] == "Logged out from 1 sessions"

    revoked_response = client.get(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {refreshed_access_token}"},
    )
    assert revoked_response.status_code == 401


def test_login_rejects_invalid_credentials(client, create_user):
    user = create_user(email="bad-login@example.com", username="bad_login")

    response = client.post(
        "/api/v1/auth/login",
        json={"email": user["email"], "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_delete_account_removes_user(client, create_authenticated_user):
    auth_user = create_authenticated_user(
        email="delete-me@example.com",
        username="delete_me",
    )

    response = client.delete(
        "/api/v1/auth/account",
        headers=auth_user["headers"],
    )

    assert response.status_code == 200
    assert response.json()["message"] == "User account deleted successfully"

    async def _load_user():
        async with session_pool() as session:
            return (
                await session.execute(select(User).where(User.id == auth_user["id"]))
            ).scalar_one_or_none()

    assert asyncio.run(_load_user()) is None
