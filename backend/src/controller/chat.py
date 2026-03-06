import json
from fastapi import HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import List
from langchain_core.documents import Document
from ..schema.chat import ChatQueryRequest
from ..schema.message import MessageCreate
from ..schema.source import SourceCreate
from ..core.chat_engine.query import ChatEngine
from ..core.logger import SingletonLogger
from ..controller import message as message_controller
from ..controller import source as source_controller

logger = SingletonLogger().get_logger()


async def query_paper(user_id: int, payload: ChatQueryRequest, request: Request):
    """
    Query a paper using the chat engine with conversation history.
    Automatically saves user query and assistant response to message table.

    Args:
        user_id: ID of the user making the query
        payload: ChatQueryRequest containing query and parameters
        request: FastAPI Request object to access app state

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
        graph = request.app.state.graph

        async def stream_and_save():
            final_response = ""
            response_metadata = {}
            retrieved_docs: List[Document] = []
            web_search_results: List[Document] = []

            try:
                response_stream = ChatEngine.generate_response(
                    graph=graph,
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

                async for chunk in response_stream:
                    yield chunk

                    try:
                        if chunk.startswith("data: "):
                            data_str = chunk[6:].strip()
                            if data_str:
                                data = json.loads(data_str)

                                if isinstance(data, list) and len(data) == 2:
                                    message_type, stream_payload = data

                                    if message_type == "updates" and isinstance(
                                        stream_payload, dict
                                    ):
                                        # Extract retrieved docs from rerank node
                                        if "rerank_docs_node" in stream_payload:
                                            node_data = stream_payload[
                                                "rerank_docs_node"
                                            ]
                                            if "retrieved_docs" in node_data:
                                                # Convert dict back to Document objects
                                                retrieved_docs = [
                                                    Document(
                                                        page_content=doc.get(
                                                            "page_content", ""
                                                        ),
                                                        metadata=doc.get(
                                                            "metadata", {}
                                                        ),
                                                    )
                                                    for doc in node_data.get(
                                                        "retrieved_docs", []
                                                    )
                                                    if isinstance(doc, dict)
                                                ]

                                        # Extract web search results from web crawl node
                                        if "web_crawl_node" in stream_payload:
                                            node_data = stream_payload["web_crawl_node"]
                                            if "web_search_results" in node_data:
                                                # Convert dict back to Document objects
                                                web_search_results = [
                                                    Document(
                                                        page_content=doc.get(
                                                            "page_content", ""
                                                        ),
                                                        metadata=doc.get(
                                                            "metadata", {}
                                                        ),
                                                    )
                                                    for doc in node_data.get(
                                                        "web_search_results", []
                                                    )
                                                    if isinstance(doc, dict)
                                                ]

                                        # Extract final response
                                        if "generate_response_node" in stream_payload:
                                            node_data = stream_payload[
                                                "generate_response_node"
                                            ]
                                            if "response" in node_data:
                                                final_response = node_data["response"]
                                            if "response_metadata" in node_data:
                                                response_metadata = node_data[
                                                    "response_metadata"
                                                ]
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.debug(
                            f"Could not parse chunk for response extraction: {e}"
                        )
                        continue

                if final_response:
                    try:
                        # Save the message first
                        assistant_message_payload = MessageCreate(
                            session_id=payload.session_id,
                            user_id=user_id,
                            content=[
                                {"role": "user", "content": payload.query},
                                {"role": "assistant", "content": final_response},
                            ],
                            parent_message_id=None,
                            model_used=payload.model_name,
                            generation_metadata=response_metadata,
                        )
                        assistant_message = await message_controller.create_message(
                            user_id, assistant_message_payload
                        )
                        logger.info(
                            f"Saved assistant message with id: {assistant_message.id}"
                        )

                        # Prepare and save sources
                        sources_to_create: List[SourceCreate] = []

                        # Add retrieved document sources
                        for doc in retrieved_docs:
                            # Extract page number if available
                            metadata = {}
                            if "page_number" in doc.metadata:
                                metadata["page_number"] = doc.metadata["page_number"]
                            if "page" in doc.metadata:
                                metadata["page"] = doc.metadata["page"]

                            sources_to_create.append(
                                SourceCreate(
                                    message_id=assistant_message.id,
                                    source_text=doc.page_content[
                                        :5000
                                    ],  # Limit text length
                                    source_type="document",
                                    source_url=doc.metadata.get("source", ""),
                                    metadata=metadata if metadata else None,
                                )
                            )

                        # Add web search result sources
                        for doc in web_search_results:
                            sources_to_create.append(
                                SourceCreate(
                                    message_id=assistant_message.id,
                                    source_text=doc.page_content[
                                        :5000
                                    ],  # Limit text length
                                    source_type="web",
                                    source_url=doc.metadata.get("url", ""),
                                )
                            )

                        # Save all sources in bulk
                        if sources_to_create:
                            saved_sources = await source_controller.create_sources(
                                sources_to_create
                            )
                            logger.info(
                                f"Saved {len(saved_sources)} sources for message {assistant_message.id}"
                            )

                    except Exception as e:
                        logger.error(
                            f"Failed to save assistant message or sources: {e}"
                        )

            except Exception as e:
                logger.error(f"Error in stream_and_save: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(
            stream_and_save(),
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
