from typing import Optional
from pydantic import BaseModel, Field


class PaperIngest(BaseModel):
    paper_url: str
    embedding_model: Optional[str] = "embed-multilingual-v3.0"
    arxiv_id: Optional[str] = None


class PaperDelete(BaseModel):
    paper_ids: list[str] = Field(..., min_length=1)
