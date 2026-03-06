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
                },
                stream_mode=["updates", "custom"],
            )
            async for update in response:
                try:
                    json_str = json.dumps(update, default=json_serializer)
                    yield f"data: {json_str}\n\n"
                except Exception as e:
                    logger.error(f"Error serializing update: {e}")
                    yield f"data: {json.dumps({'error': 'Serialization error'})}\n\n"
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise e
