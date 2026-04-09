from fastapi import APIRouter, Depends, Request

from ..controller.ingestion import ingest_paper, delete_paper
from ..schema.ingestion import PaperIngest, PaperDelete
from ..lib.auth import get_current_user
from ..lib.api_key_middleware import load_user_api_keys


router = APIRouter()


@router.post("/ingest", response_model=dict)
async def ingest_paper_endpoint(
    payload: PaperIngest,
    request: Request,
    user_id: int = Depends(get_current_user),
    _: int = Depends(load_user_api_keys),
):
    """Ingest a paper into the vector store."""
    return await ingest_paper(payload, user_id, request)


@router.delete("/delete", response_model=dict)
async def delete_paper_endpoint(
    payload: PaperDelete,
    request: Request,
    user_id: int = Depends(get_current_user),
    _: int = Depends(load_user_api_keys),
):
    """Delete a paper from the vector store."""
    return await delete_paper(payload, user_id, request)
