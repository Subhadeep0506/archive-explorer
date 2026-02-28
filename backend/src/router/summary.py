from fastapi import APIRouter, Depends

from ..controller import summary as summary_controller
from ..schema.summary import SummaryResponse, UsabilityResponse
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
    """Generate a summary for a specific paper."""
    summary = await summary_controller.generate_paper_summary(arxiv_id)
    return SummaryResponse(arxiv_id=arxiv_id, summary=summary)


@router.post("/{arxiv_id}/usability", response_model=UsabilityResponse)
async def generate_usability(arxiv_id: str, user_id: int = Depends(get_current_user)):
    """Generate usability metrics for a specific paper."""
    usability_data = await summary_controller.generate_paper_usability(
        arxiv_id, user_id
    )
    return UsabilityResponse(
        arxiv_id=arxiv_id,
        domain_applicability=usability_data.get("domain_applicability", {}),
        reproducibility_score=usability_data.get("reproducibility_score", 0.0),
        new_tech_applicability=usability_data.get("new_tech_applicability", {}),
        impact_score=usability_data.get("impact_score"),
    )
