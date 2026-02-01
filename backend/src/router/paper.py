from fastapi import APIRouter, Depends

from ..controller.paper import create_paper
from ..schema.paper import PaperCreate, PaperResponse
from ..lib.auth import get_current_user


router = APIRouter()


@router.post("/", response_model=PaperResponse)
async def add_paper(payload: PaperCreate, user_id: int = Depends(get_current_user)):
    """Add a paper; generates and stores its thumbnail automatically."""
    return await create_paper(user_id, payload)
