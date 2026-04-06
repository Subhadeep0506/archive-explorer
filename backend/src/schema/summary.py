from pydantic import BaseModel, field_validator
from typing import Dict, Optional
from .user_settings import ApiKeyItem


class SummaryResponse(BaseModel):
    arxiv_id: str
    summary: str


class SummaryGenerateRequest(BaseModel):
    arxiv_id: Optional[str] = None
    pdf_url: Optional[str] = None
    api_keys_encrypted: Optional[list[ApiKeyItem]] = None

    @field_validator("arxiv_id", "pdf_url")
    @classmethod
    def check_at_least_one(cls, v, info):
        return v

    def model_post_init(self, __context) -> None:
        if not self.arxiv_id and not self.pdf_url:
            raise ValueError("Either arxiv_id or pdf_url must be provided")


class UsabilityGenerateRequest(BaseModel):
    arxiv_id: Optional[str] = None
    pdf_url: Optional[str] = None
    api_keys_encrypted: Optional[list[ApiKeyItem]] = None

    @field_validator("arxiv_id", "pdf_url")
    @classmethod
    def check_at_least_one(cls, v, info):
        return v

    def model_post_init(self, __context) -> None:
        if not self.arxiv_id and not self.pdf_url:
            raise ValueError("Either arxiv_id or pdf_url must be provided")


class UsabilityResponse(BaseModel):
    arxiv_id: Optional[str] = None
    pdf_url: Optional[str] = None
    domain_applicability: Dict[str, float]
    reproducibility_score: Dict[str, float]
    new_tech_applicability: Dict[str, float]
    impact_score: Optional[float]
