from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class PaperCreate(BaseModel):
    title: str
    abstract: str
    authors: str
    arxiv_id: str
    pdf_url: str
    paper_url: Optional[str] = None
    github_url: Optional[str] = None
    topics: Optional[str] = None
    published_date: Optional[str] = None
    institution: Optional[str] = None
    date_published: Optional[str] = None
    thumbnail_url: Optional[str] = None


class PaperResponse(BaseModel):
    id: int
    user_id: int
    title: str
    abstract: str
    authors: str
    arxiv_id: str
    pdf_url: str
    paper_url: Optional[str] = None
    github_url: Optional[str] = None
    topics: Optional[str] = None
    published_date: Optional[str] = None
    thumbnail_url: Optional[str] = None
    institution: Optional[str] = None
    date_published: Optional[str] = None
    created_at: datetime
    ingested: bool
    paper_summary: Optional[str] = None


class BulkDeletePapers(BaseModel):
    paper_ids: list[int]
