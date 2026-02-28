from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from ..schema.chat import ChatQueryRequest
from ..core.chat_engine.query import ChatEngine
from ..core.logger import SingletonLogger

logger = SingletonLogger().get_logger()


async def query_paper(user_id: int, payload: ChatQueryRequest):
    """
    Query a paper using the chat engine with conversation history.

    Args:
        user_id: ID of the user making the query
        payload: ChatQueryRequest containing query parameters

    Returns:
        StreamingResponse with SSE updates from the LangGraph execution

    Raises:
        HTTPException: If there's an error processing the query
    """
    try:
        logger.info(
            f"User {user_id} querying paper {payload.paper_id} "
            f"in session {payload.session_id}: {payload.query}"
        )

        # Generate response using the chat engine
        response_stream = ChatEngine.generate_response(
            query=payload.query,
            user_id=user_id,
            thread_id=payload.session_id,
            paper_id=payload.paper_id,
            model_name=payload.model_name,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
            top_k=payload.top_k,
            use_web_search=payload.use_web_search,
            web_search_topic=payload.web_search_topic,
        )

        # Return streaming response
        return StreamingResponse(
            response_stream,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    except Exception as e:
        logger.exception(f"Error querying paper: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
