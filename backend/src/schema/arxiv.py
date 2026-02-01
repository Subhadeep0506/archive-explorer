from typing import List, Optional
from pydantic import BaseModel, Field


class ArxivEntry(BaseModel):
    id: Optional[str] = None
    arxiv_id: Optional[str] = None
    title: Optional[str] = None
    abstract: Optional[str] = Field(default=None, alias="summary")
    authors: List[str] = []
    pdf_url: Optional[str] = None
    paper_url: Optional[str] = None
    categories: List[str] = []
    primary_category: Optional[str] = None
    published: Optional[str] = None
    updated: Optional[str] = None
    comment: Optional[str] = None
    journal_ref: Optional[str] = None
    doi: Optional[str] = None
    thumbnail_url: Optional[str] = None

    class Config:
        populate_by_name = True


class ThumbnailRequest(BaseModel):
    pdf_url: str
    target_width: Optional[int] = 400
    folder: Optional[str] = "thumbnails"


class ThumbnailResponse(BaseModel):
    thumbnail_url: Optional[str]
