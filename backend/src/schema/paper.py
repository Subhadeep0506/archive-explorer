from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class PaperCreate(BaseModel):
    title: str
    abstract: str
    authors: str
    arxiv_id: Optional[str] = None
    pdf_url: Optional[str] = None
    paper_url: Optional[str] = None
    github_url: Optional[str] = None
    topics: Optional[str] = None
    published_date: Optional[str] = None
    institution: Optional[str] = None
    date_published: Optional[str] = None
    thumbnail_url: Optional[str] = None
    paper_source: Optional[str] = "arxiv"


class PaperUploadMetadata(BaseModel):
    """Metadata for uploaded PDF papers (non-arxiv)"""

    title: str
    abstract: str
    authors: str
    # Optional fields
    github_url: Optional[str] = None
    topics: Optional[str] = None
    published_date: Optional[str] = None
    institution: Optional[str] = None
    date_published: Optional[str] = None


class PaperResponse(BaseModel):
    id: int
    user_id: int
    title: str
    abstract: str
    authors: str
    arxiv_id: Optional[str] = None
    pdf_url: Optional[str] = None
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
    paper_source: Optional[str] = "arxiv"
    keywords: Optional[str] = None


class BulkDeletePapers(BaseModel):
    paper_ids: list[int]


class RecommendationItem(BaseModel):
    arxiv_id: Optional[str] = None
    title: Optional[str] = None
    authors: Optional[str] = None
    categories: Optional[str] = None
    primary_category: Optional[str] = None
    published_date: Optional[str] = None
    paper_url: Optional[str] = None
    pdf_url: Optional[str] = None
    score: Optional[float] = None
    final_score: Optional[float] = None


class RecommendationsResponse(BaseModel):
    similar_papers: list[RecommendationItem] = []
    on_this_topic: list[RecommendationItem] = []
    from_these_authors: list[RecommendationItem] = []
