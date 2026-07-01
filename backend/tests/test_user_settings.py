import asyncio

from sqlalchemy import select

from src.database.db import session_pool
from src.model import UserSettings


def test_get_user_settings_creates_defaults(client, create_authenticated_user):
    auth_user = create_authenticated_user(with_settings=False)

    response = client.get("/api/v1/settings/", headers=auth_user["headers"])

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == auth_user["id"]
    assert payload["api_keys_encrypted"] is None

    async def _load_settings():
        async with session_pool() as session:
            return (
                await session.execute(
                    select(UserSettings).where(UserSettings.user_id == auth_user["id"])
                )
            ).scalar_one_or_none()

    assert asyncio.run(_load_settings()) is not None


def test_update_user_settings_encrypts_plaintext_api_keys(
    client, create_authenticated_user
):
    auth_user = create_authenticated_user(with_settings=False)
    plaintext_key = "sk-test-plaintext"

    response = client.put(
        "/api/v1/settings/",
        headers=auth_user["headers"],
        json={
            "location": "Bengaluru",
            "custom_summary_instructions": "Focus on practical takeaways",
            "api_keys_encrypted": [
                {
                    "id": 1,
                    "slug": "openai",
                    "name": "OpenAI",
                    "api_key": plaintext_key,
                }
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["location"] == "Bengaluru"
    assert payload["api_keys_encrypted"][0]["api_key"] != plaintext_key

    async def _load_settings():
        async with session_pool() as session:
            return (
                await session.execute(
                    select(UserSettings).where(UserSettings.user_id == auth_user["id"])
                )
            ).scalar_one()

    settings = asyncio.run(_load_settings())
    assert settings.api_keys_encrypted[0]["api_key"] != plaintext_key
    assert settings.api_keys[0]["api_key"] == plaintext_key


def test_update_user_settings_clears_keys_with_empty_list(
    client, create_authenticated_user
):
    auth_user = create_authenticated_user(with_settings=True)

    initial_response = client.put(
        "/api/v1/settings/",
        headers=auth_user["headers"],
        json={
            "api_keys_encrypted": [
                {
                    "id": 1,
                    "slug": "openai",
                    "name": "OpenAI",
                    "api_key": "sk-initial",
                }
            ]
        },
    )
    assert initial_response.status_code == 200

    clear_response = client.put(
        "/api/v1/settings/",
        headers=auth_user["headers"],
        json={"api_keys_encrypted": []},
    )

    assert clear_response.status_code == 200
    assert clear_response.json()["api_keys_encrypted"] == []

    async def _load_settings():
        async with session_pool() as session:
            return (
                await session.execute(
                    select(UserSettings).where(UserSettings.user_id == auth_user["id"])
                )
            ).scalar_one()

    settings = asyncio.run(_load_settings())
    assert settings.api_keys_encrypted == []


def test_get_services_and_resources_only_returns_active_entries(
    client, create_authenticated_user, seed_catalog
):
    auth_user = create_authenticated_user()
    seed_catalog()

    services_response = client.get(
        "/api/v1/settings/services",
        headers=auth_user["headers"],
    )
    resources_response = client.get(
        "/api/v1/settings/resources",
        headers=auth_user["headers"],
    )

    assert services_response.status_code == 200
    services = services_response.json()
    assert len(services) == 1
    assert services[0]["slug"] == "openai"

    assert resources_response.status_code == 200
    resources = resources_response.json()
    assert len(resources) == 1
    assert resources[0]["slug"] == "gpt-4.1"
    assert resources[0]["service_slug"] == "openai"
    assert resources[0]["service_name"] == "OpenAI"
