import asyncio

from sqlalchemy import select

from src.database.db import session_pool
from src.model import Paper


def build_paper_payload(**overrides):
    payload = {
        "title": "Attention Is All You Need",
        "abstract": "Transformers replace recurrence with attention.",
        "authors": "A. Researcher, B. Scientist",
        "arxiv_id": "1706.03762",
        "pdf_url": "https://example.com/papers/attention.pdf",
        "paper_url": "https://arxiv.org/abs/1706.03762",
        "github_url": "https://github.com/example/attention",
        "topics": "transformers, attention",
        "published_date": "2017-06-12",
        "institution": "Example Lab",
        "date_published": "2017-06-12",
        "paper_source": "arxiv",
    }
    payload.update(overrides)
    return payload


def test_list_papers_returns_empty_list(client, create_authenticated_user):
    auth_user = create_authenticated_user()

    response = client.get("/api/v1/papers/", headers=auth_user["headers"])

    assert response.status_code == 200
    assert response.json() == []


def test_create_paper_and_fetch_by_id(
    client, create_authenticated_user, external_service_spies
):
    auth_user = create_authenticated_user()

    create_response = client.post(
        "/api/v1/papers/",
        headers=auth_user["headers"],
        json=build_paper_payload(),
    )

    assert create_response.status_code == 200
    created_paper = create_response.json()
    assert created_paper["title"] == "Attention Is All You Need"
    assert created_paper["thumbnail_url"] == "https://thumbs.example/1.png"
    assert external_service_spies["background_index"]

    get_response = client.get(
        f"/api/v1/papers/{created_paper['id']}",
        headers=auth_user["headers"],
    )
    assert get_response.status_code == 200
    assert get_response.json()["arxiv_id"] == "1706.03762"


def test_protected_paper_route_rejects_invalid_token(client):
    response = client.get(
        "/api/v1/papers/",
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_create_paper_rejects_duplicate_arxiv_id(client, create_authenticated_user):
    first_user = create_authenticated_user()
    second_user = create_authenticated_user()

    first_response = client.post(
        "/api/v1/papers/",
        headers=first_user["headers"],
        json=build_paper_payload(),
    )
    assert first_response.status_code == 200

    duplicate_response = client.post(
        "/api/v1/papers/",
        headers=second_user["headers"],
        json=build_paper_payload(title="Duplicate title"),
    )
    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == "Paper already exists"


def test_thumbnail_generation_failure_is_non_fatal(
    client, create_authenticated_user, monkeypatch
):
    auth_user = create_authenticated_user()

    async def failing_thumbnail(*args, **kwargs):
        raise RuntimeError("thumbnail failed")

    monkeypatch.setattr(
        "src.controller.paper.generate_first_page_thumbnail", failing_thumbnail
    )

    response = client.post(
        "/api/v1/papers/",
        headers=auth_user["headers"],
        json=build_paper_payload(arxiv_id="2401.00001"),
    )

    assert response.status_code == 200
    assert response.json()["thumbnail_url"] is None


def test_fetching_other_users_paper_returns_404(
    client, create_authenticated_user, create_paper_record
):
    owner = create_authenticated_user()
    stranger = create_authenticated_user()
    paper = create_paper_record(user_id=owner["id"], arxiv_id="2401.00002")

    response = client.get(
        f"/api/v1/papers/{paper['id']}",
        headers=stranger["headers"],
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Paper not found"


def test_delete_paper_is_non_fatal_when_cleanup_fails(
    client, create_authenticated_user, create_paper_record, monkeypatch
):
    auth_user = create_authenticated_user()
    paper = create_paper_record(user_id=auth_user["id"], arxiv_id="2401.00003")

    async def failing_cleanup(arxiv_ids):
        raise RuntimeError("cleanup failed")

    monkeypatch.setattr(
        "src.controller.paper.IngestionEngine.delete_paper_using_paper_ids",
        failing_cleanup,
    )

    response = client.delete(
        f"/api/v1/papers/{paper['id']}",
        headers=auth_user["headers"],
    )

    assert response.status_code == 204

    async def _load_paper():
        async with session_pool() as session:
            return (
                await session.execute(select(Paper).where(Paper.id == paper["id"]))
            ).scalar_one_or_none()

    assert asyncio.run(_load_paper()) is None


def test_bulk_delete_returns_404_for_missing_papers(client, create_authenticated_user):
    auth_user = create_authenticated_user()

    response = client.delete(
        "/api/v1/papers/bulk?paper_ids=999&paper_ids=1000",
        headers=auth_user["headers"],
    )

    assert response.status_code == 404
    assert "Papers not found" in response.json()["detail"]
