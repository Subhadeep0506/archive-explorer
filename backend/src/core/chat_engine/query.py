import json
import os
import asyncio
import sys
from fastapi import FastAPI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from .agent_state import AgentState
from .agents import (
    generate_response_node,
    context_retriever_node,
    rerank_docs_node,
    web_crawl_node,
)
from ...core.logger import SingletonLogger

# Fix for Windows: Replace ProactorEventLoop with SelectorEventLoop for psycopg async
if sys.platform == "win32":
    import selectors

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No loop is running, set the policy for future loops
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def router_from_retriever(state: AgentState):
    """Route based on whether web search is to be done or not."""
    if state.get("use_web_search", False):
        return "web_crawl_node"
    return "rerank_docs_node"


def json_serializer(obj):
    """Custom JSON serializer for objects not serializable by default json code"""
    from langchain_core.documents import Document

    if isinstance(obj, Document):
        return {"metadata": obj.metadata, "page_content": obj.page_content}
    try:
        return str(obj)
    except Exception:
        return None


class ChatEngine:
    @staticmethod
    async def build_graph():
        """Build and return the compiled graph with the provided checkpointer."""
        try:
            builder = StateGraph(AgentState)
            builder.add_node("context_retriever_node", context_retriever_node)
            builder.add_node("web_crawl_node", web_crawl_node)
            builder.add_node("rerank_docs_node", rerank_docs_node)
            builder.add_node("generate_response_node", generate_response_node)

            builder.add_edge(START, "context_retriever_node")
            builder.add_conditional_edges(
                "context_retriever_node",
                router_from_retriever,
                {
                    "web_crawl_node": "web_crawl_node",
                    "rerank_docs_node": "rerank_docs_node",
                },
            )
            builder.add_edge("web_crawl_node", "rerank_docs_node")
            builder.add_edge("rerank_docs_node", "generate_response_node")
            builder.add_edge("generate_response_node", END)

            graph = builder.compile()
            return graph
        except Exception as e:
            logger = SingletonLogger().get_logger()
            logger.error(f"Error building graph: {e}")
            raise e

    @staticmethod
    async def generate_response(
        graph: CompiledStateGraph,
        query: str,
        user_id: int,
        thread_id: int,
        paper_id: str,
        model_name: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_k: int = 5,
        use_web_search: bool = False,
        web_search_topic: str = "general",
        request=None,
    ):
        logger = SingletonLogger().get_logger()
        try:
            response = graph.astream(
                {
                    "conversation_id": thread_id,
                    "paper_id": paper_id,
                    "paper_title": "",
                    "paper_authors": "",
                    "user_id": user_id,
                    "messages": [],
                    "query": query,
                    "model_name": model_name,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "top_k": top_k,
                    "use_web_search": use_web_search,
                    "web_search_topic": web_search_topic,
                    "retrieved_docs": [],
                    "doc_relevance_scores": [],
                    "web_search_results": [],
                    "response": "",
                    "response_metadata": {},
                    "request": request,
                },
                stream_mode=["updates", "custom", "messages"],
                version="v2",
            )
            async for chunk in response:
                try:
                    # Handle both v2 dict format and v1 tuple format
                    if isinstance(chunk, dict):
                        # v2 format: {"type": "...", "ns": (), "data": ...}
                        chunk_type = chunk.get("type")
                        chunk_data = chunk.get("data")

                        if chunk_type == "messages":
                            # Messages stream: (message_chunk, metadata)
                            msg, metadata = chunk_data
                            if hasattr(msg, "content") and msg.content:
                                # Extract text from content (may be string or list of dicts)
                                text_content = ""
                                if isinstance(msg.content, str):
                                    text_content = msg.content
                                elif isinstance(msg.content, list):
                                    # Extract text from list of content blocks
                                    for block in msg.content:
                                        if (
                                            isinstance(block, dict)
                                            and block.get("type") == "text"
                                        ):
                                            text_content += block.get("text", "")

                                if text_content:
                                    # Stream LLM tokens
                                    yield f"data: {json.dumps({'type': 'token', 'content': text_content})}\n\n"
                        elif chunk_type == "updates":
                            # State updates from nodes
                            yield f"data: {json.dumps({'type': 'updates', 'data': chunk_data}, default=json_serializer)}\n\n"
                        elif chunk_type == "custom":
                            # Custom events (status messages)
                            yield f"data: {json.dumps({'type': 'custom', 'data': chunk_data})}\n\n"

                    elif isinstance(chunk, tuple) and len(chunk) >= 2:
                        # v1 format: (mode, data) tuples
                        mode, data = chunk[0], chunk[1]

                        if mode == "messages":
                            # Messages: (message_chunk, metadata)
                            msg, metadata = data
                            if hasattr(msg, "content") and msg.content:
                                # Extract text from content (may be string or list of dicts)
                                text_content = ""
                                if isinstance(msg.content, str):
                                    text_content = msg.content
                                elif isinstance(msg.content, list):
                                    # Extract text from list of content blocks
                                    for block in msg.content:
                                        if (
                                            isinstance(block, dict)
                                            and block.get("type") == "text"
                                        ):
                                            text_content += block.get("text", "")

                                if text_content:
                                    yield f"data: {json.dumps({'type': 'token', 'content': text_content})}\n\n"
                        elif mode == "updates":
                            yield f"data: {json.dumps({'type': 'updates', 'data': data}, default=json_serializer)}\n\n"
                        elif mode == "custom":
                            yield f"data: {json.dumps({'type': 'custom', 'data': data})}\n\n"

                except Exception as e:
                    logger.error(f"Error serializing chunk: {e}")
                    logger.debug(f"Chunk type: {type(chunk)}, Chunk: {chunk}")
                    yield f"data: {json.dumps({'error': 'Serialization error'})}\n\n"
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise e
