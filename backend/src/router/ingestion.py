from fastapi import APIRouter, Depends

from ..controller.ingestion import ingest_paper, delete_paper
from ..schema.ingestion import PaperIngest, PaperDelete
from ..lib.auth import get_current_user


router = APIRouter()


@router.post("/ingest", response_model=dict)
async def ingest_paper_endpoint(
    payload: PaperIngest, user_id: int = Depends(get_current_user)
):
    """Ingest a paper into the vector store."""
    return await ingest_paper(payload, user_id)


@router.delete("/delete", response_model=dict)
async def delete_paper_endpoint(
    payload: PaperDelete, user_id: int = Depends(get_current_user)
):
    """Delete a paper from the vector store."""
    return await delete_paper(payload, user_id)
