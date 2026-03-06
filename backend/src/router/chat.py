from fastapi import APIRouter, Depends, Request

from ..controller import chat as chat_controller
from ..schema.chat import ChatQueryRequest
from ..lib.auth import get_current_user


router = APIRouter()


@router.post("/query")
async def query_paper_endpoint(
    payload: ChatQueryRequest,
    request: Request,
    user_id: int = Depends(get_current_user),
):
    """
    Query a paper with conversation history using LangGraph.

    Streams back the LangGraph execution updates as Server-Sent Events (SSE).
    The conversation history is automatically maintained via checkpointing
    using the session_id as the thread_id.

    Automatically saves both the user query and assistant response to the message table.

    Args:
        payload: ChatQueryRequest containing query and parameters
        request: FastAPI Request object
        user_id: Current authenticated user ID (from JWT token)

    Returns:
        StreamingResponse with SSE updates showing the progress through
        the LangGraph nodes (retrieval, web search, reranking, generation)
    """
    return await chat_controller.query_paper(user_id, payload, request)
