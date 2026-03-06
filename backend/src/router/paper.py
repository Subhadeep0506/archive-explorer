from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from typing import List

from ..controller import paper as paper_controller
from ..schema.paper import PaperCreate, PaperResponse
from ..lib.auth import get_current_user


router = APIRouter()


@router.get("/", response_model=list[PaperResponse])
async def get_saved_papers(user_id: int = Depends(get_current_user)):
    """Retrieve all saved papers for the current user."""
    return await paper_controller.get_all_papers(user_id)


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_saved_paper(paper_id: int, user_id: int = Depends(get_current_user)):
    """Retrieve a specific saved paper by ID for the current user."""
    return await paper_controller.get_paper(paper_id, user_id)


@router.post("/", response_model=PaperResponse)
async def add_paper(payload: PaperCreate, user_id: int = Depends(get_current_user)):
    """Add a paper; generates and stores its thumbnail automatically."""
    return await paper_controller.create_paper(user_id, payload)


@router.post("/upload", response_model=PaperResponse)
async def upload_paper_pdf(
    file: UploadFile = File(...),
    title: str = Form(...),
    abstract: str = Form(...),
    authors: str = Form(...),
    github_url: str = Form(None),
    topics: str = Form(None),
    published_date: str = Form(None),
    institution: str = Form(None),
    date_published: str = Form(None),
    user_id: int = Depends(get_current_user),
):
    """Upload a custom PDF paper with metadata. The PDF will be stored and made available for ingestion."""
    return await paper_controller.create_paper_from_upload(
        user_id=user_id,
        file=file,
        title=title,
        abstract=abstract,
        authors=authors,
        github_url=github_url,
        topics=topics,
        published_date=published_date,
        institution=institution,
        date_published=date_published,
    )


@router.delete("/bulk", response_model=dict)
async def bulk_delete_papers_endpoint(
    paper_ids: List[int] = Query([]),
    user_id: int = Depends(get_current_user),
):
    """Delete multiple papers by IDs for the current user."""
    return await paper_controller.bulk_delete_papers(paper_ids, user_id)


@router.delete("/{paper_id}", status_code=204)
async def delete_saved_paper(paper_id: int, user_id: int = Depends(get_current_user)):
    """Delete a saved paper by ID for the current user."""
    await paper_controller.delete_paper(paper_id, user_id)
