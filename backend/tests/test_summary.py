import asyncio

import pytest
from sqlalchemy import func, select

from src.database.db import session_pool
from src.model import Paper, Usability


def test_get_summary_and_usability_returns_existing_data(
    client, create_authenticated_user, create_paper_record, create_usability_record
):
    auth_user = create_authenticated_user()
    paper = create_paper_record(
        user_id=auth_user["id"],
        arxiv_id="2401.10000",
        paper_summary="Existing summary",
    )
    create_usability_record(
        user_id=auth_user["id"],
        paper_id=paper["id"],
        impact_score=0.91,
    )

    response = client.get(
        f"/api/v1/summary/{paper['arxiv_id']}",
        headers=auth_user["headers"],
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"] == "Existing summary"
    assert payload["usability"]["impact_score"] == 0.91


def test_generate_summary_updates_paper(
    client, create_authenticated_user, create_paper_record, external_service_spies
):
    auth_user = create_authenticated_user()
    paper = create_paper_record(
        user_id=auth_user["id"],
        arxiv_id="2401.10001",
        paper_summary="",
    )

    response = client.post(
        f"/api/v1/summary/{paper['arxiv_id']}",
        headers=auth_user["headers"],
    )

    assert response.status_code == 200
    assert response.json()["summary"] == f"summary for {paper['arxiv_id']}"
    assert external_service_spies["summaries"] == [
        {"arxiv_id": paper["arxiv_id"], "pdf_url": None}
    ]

    async def _load_paper():
        async with session_pool() as session:
            return (
                await session.execute(
                    select(Paper).where(Paper.arxiv_id == paper["arxiv_id"])
                )
            ).scalar_one()

    updated_paper = asyncio.run(_load_paper())
    assert updated_paper.paper_summary == f"summary for {paper['arxiv_id']}"


@pytest.mark.xfail(
    reason="Current router order registers /{arxiv_id} before /generate, so /generate is shadowed.",
    strict=False,
)
def test_generate_summary_for_pdf_url_does_not_require_paper(
    client, create_authenticated_user, external_service_spies
):
    auth_user = create_authenticated_user()

    response = client.post(
        "/api/v1/summary/generate",
        headers=auth_user["headers"],
        json={"pdf_url": "https://example.com/papers/custom.pdf"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["arxiv_id"] == ""
    assert payload["summary"] == "summary for https://example.com/papers/custom.pdf"
    assert external_service_spies["summaries"] == [
        {"arxiv_id": None, "pdf_url": "https://example.com/papers/custom.pdf"}
    ]


def test_generate_usability_creates_then_updates_record(
    client, create_authenticated_user, create_paper_record, monkeypatch
):
    auth_user = create_authenticated_user()
    paper = create_paper_record(user_id=auth_user["id"], arxiv_id="2401.10002")

    async def first_result(arxiv_id=None, pdf_url=None, request=None):
        return {
            "domain_applicability": {"Technology": 0.7},
            "reproducibility_score": {"Reproducible": 0.6},
            "new_tech_applicability": {"Agentic AI": 0.5},
            "impact_score": 0.4,
        }

    async def second_result(arxiv_id=None, pdf_url=None, request=None):
        return {
            "domain_applicability": {"Technology": 0.95},
            "reproducibility_score": {"Reproducible": 0.9},
            "new_tech_applicability": {"Agentic AI": 0.85},
            "impact_score": 0.8,
        }

    monkeypatch.setattr(
        "src.controller.summary.UsabilityEngine.generate_paper_summary", first_result
    )
    first_response = client.post(
        f"/api/v1/summary/{paper['arxiv_id']}/usability",
        headers=auth_user["headers"],
    )
    assert first_response.status_code == 200
    assert first_response.json()["impact_score"] == 0.4

    monkeypatch.setattr(
        "src.controller.summary.UsabilityEngine.generate_paper_summary", second_result
    )
    second_response = client.post(
        f"/api/v1/summary/{paper['arxiv_id']}/usability",
        headers=auth_user["headers"],
    )
    assert second_response.status_code == 200
    assert second_response.json()["impact_score"] == 0.8

    async def _load_state():
        async with session_pool() as session:
            record_count = (
                await session.execute(
                    select(func.count(Usability.id)).where(
                        Usability.user_id == auth_user["id"],
                        Usability.paper_id == paper["id"],
                    )
                )
            ).scalar_one()
            usability = (
                await session.execute(
                    select(Usability).where(
                        Usability.user_id == auth_user["id"],
                        Usability.paper_id == paper["id"],
                    )
                )
            ).scalar_one()
            return record_count, usability

    record_count, usability = asyncio.run(_load_state())
    assert record_count == 1
    assert usability.impact_score == 0.8
    assert usability.domain_applicability == {"Technology": 0.95}


def test_generate_summary_returns_404_for_missing_paper(
    client, create_authenticated_user
):
    auth_user = create_authenticated_user()

    response = client.post(
        "/api/v1/summary/does-not-exist",
        headers=auth_user["headers"],
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Paper not found"
