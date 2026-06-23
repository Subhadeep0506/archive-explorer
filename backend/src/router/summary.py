from fastapi import APIRouter, Depends, Request

from ..controller import summary as summary_controller
from ..schema.summary import (
    SummaryResponse,
    SummaryGenerateRequest,
    UsabilityResponse,
    UsabilityGenerateRequest,
)
from ..lib.auth import get_current_user
from ..lib.api_key_middleware import load_user_api_keys


router = APIRouter()


# Static routes MUST be registered before parametric /{arxiv_id} routes
# to avoid path shadowing (e.g. POST /generate matching /{arxiv_id}).


@router.post("/generate", response_model=SummaryResponse)
async def generate_summary_flexible(
    payload: SummaryGenerateRequest,
    request: Request,
    user_id: int = Depends(get_current_user),
    _: int = Depends(load_user_api_keys),
):
    """Generate a summary for a paper using arxiv_id or pdf_url."""
    summary = await summary_controller.generate_paper_summary(
        user_id=user_id,
        arxiv_id=payload.arxiv_id,
        pdf_url=payload.pdf_url,
        request=request,
    )
    return SummaryResponse(arxiv_id=payload.arxiv_id or "", summary=summary)


@router.post("/usability/generate", response_model=UsabilityResponse)
async def generate_usability_flexible(
    payload: UsabilityGenerateRequest,
    request: Request,
    user_id: int = Depends(get_current_user),
    _: int = Depends(load_user_api_keys),
):
    """Generate usability metrics for a paper using arxiv_id or pdf_url."""
    usability_data = await summary_controller.generate_paper_usability(
        user_id=user_id,
        arxiv_id=payload.arxiv_id,
        pdf_url=payload.pdf_url,
        request=request,
    )
    return UsabilityResponse(
        arxiv_id=payload.arxiv_id,
        pdf_url=payload.pdf_url,
        domain_applicability=usability_data.get("domain_applicability", {}),
        reproducibility_score=usability_data.get("reproducibility_score", {}),
        new_tech_applicability=usability_data.get("new_tech_applicability", {}),
        impact_score=usability_data.get("impact_score"),
    )


@router.get("/{arxiv_id}")
async def get_summary_and_usability(
    arxiv_id: str, user_id: int = Depends(get_current_user)
):
    """Get the summary and usability metrics for a specific paper."""
    summary = await summary_controller.get_summary_and_usability(arxiv_id, user_id)
    return {
        "arxiv_id": arxiv_id,
        "summary": summary.get("summary"),
        "usability": summary.get("usability"),
    }


@router.post("/{arxiv_id}", response_model=SummaryResponse)
async def generate_summary(
    arxiv_id: str,
    request: Request,
    user_id: int = Depends(get_current_user),
    _: int = Depends(load_user_api_keys),
):
    """Generate a summary for a specific paper (backward compatibility)."""
    summary = await summary_controller.generate_paper_summary(
        user_id=user_id, arxiv_id=arxiv_id, request=request
    )
    return SummaryResponse(arxiv_id=arxiv_id, summary=summary)


@router.post("/{arxiv_id}/usability", response_model=UsabilityResponse)
async def generate_usability(
    arxiv_id: str,
    request: Request,
    user_id: int = Depends(get_current_user),
    _: int = Depends(load_user_api_keys),
):
    """Generate usability metrics for a specific paper (backward compatibility)."""
    usability_data = await summary_controller.generate_paper_usability(
        user_id=user_id, arxiv_id=arxiv_id, request=request
    )
    return UsabilityResponse(
        arxiv_id=arxiv_id,
        domain_applicability=usability_data.get("domain_applicability", {}),
        reproducibility_score=usability_data.get("reproducibility_score", {}),
        new_tech_applicability=usability_data.get("new_tech_applicability", {}),
        impact_score=usability_data.get("impact_score"),
    )
