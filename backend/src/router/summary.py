from fastapi import APIRouter, Depends

from ..controller import summary as summary_controller
from ..schema.summary import (
    SummaryResponse,
    SummaryGenerateRequest,
    UsabilityResponse,
    UsabilityGenerateRequest,
)
from ..lib.auth import get_current_user


router = APIRouter()


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
async def generate_summary(arxiv_id: str, user_id: int = Depends(get_current_user)):
    """Generate a summary for a specific paper (backward compatibility)."""
    summary = await summary_controller.generate_paper_summary(arxiv_id=arxiv_id)
    return SummaryResponse(arxiv_id=arxiv_id, summary=summary)


@router.post("/generate", response_model=SummaryResponse)
async def generate_summary_flexible(
    request: SummaryGenerateRequest, user_id: int = Depends(get_current_user)
):
    """Generate a summary for a paper using arxiv_id or pdf_url."""
    summary = await summary_controller.generate_paper_summary(
        arxiv_id=request.arxiv_id, pdf_url=request.pdf_url
    )
    return SummaryResponse(arxiv_id=request.arxiv_id or "", summary=summary)


@router.post("/{arxiv_id}/usability", response_model=UsabilityResponse)
async def generate_usability(arxiv_id: str, user_id: int = Depends(get_current_user)):
    """Generate usability metrics for a specific paper (backward compatibility)."""
    usability_data = await summary_controller.generate_paper_usability(
        user_id=user_id, arxiv_id=arxiv_id
    )
    return UsabilityResponse(
        arxiv_id=arxiv_id,
        domain_applicability=usability_data.get("domain_applicability", {}),
        reproducibility_score=usability_data.get("reproducibility_score", {}),
        new_tech_applicability=usability_data.get("new_tech_applicability", {}),
        impact_score=usability_data.get("impact_score"),
    )


@router.post("/usability/generate", response_model=UsabilityResponse)
async def generate_usability_flexible(
    request: UsabilityGenerateRequest, user_id: int = Depends(get_current_user)
):
    """Generate usability metrics for a paper using arxiv_id or pdf_url."""
    usability_data = await summary_controller.generate_paper_usability(
        user_id=user_id, arxiv_id=request.arxiv_id, pdf_url=request.pdf_url
    )
    return UsabilityResponse(
        arxiv_id=request.arxiv_id,
        pdf_url=request.pdf_url,
        domain_applicability=usability_data.get("domain_applicability", {}),
        reproducibility_score=usability_data.get("reproducibility_score", {}),
        new_tech_applicability=usability_data.get("new_tech_applicability", {}),
        impact_score=usability_data.get("impact_score"),
    )
