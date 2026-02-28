from pydantic import BaseModel
from typing import Dict, Optional


class SummaryResponse(BaseModel):
    arxiv_id: str
    summary: str


class SummaryGenerateRequest(BaseModel):
    arxiv_id: str


class UsabilityResponse(BaseModel):
    arxiv_id: str
    domain_applicability: Dict[str, float]
    reproducibility_score: float
    new_tech_applicability: Dict[str, float]
    impact_score: Optional[float]
