from ....lib.langsearch import LangSearchClient
from ....core.logger import SingletonLogger
from ..agent_state import AgentState
from langgraph.config import get_stream_writer


async def rerank_docs_node(state: AgentState):
    """Rerank a list of documents based on relevance to the query using LangSearch API."""
    logger = SingletonLogger().get_logger()
    stream_writer = get_stream_writer()
    try:
        stream_writer(
            {
                "type": "Rerank Docs",
                "message": "Reranking documents based on relevance...",
            }
        )
        reranked_docs, doc_relevance_scores = await LangSearchClient.rerank_docs(
            query=state["query"],
            documents=state["retrieved_docs"],
            top_n=state["top_k"],
            request=state.get("request"),
        )
        stream_writer(
            {
                "type": "Rerank Docs",
                "message": "Reranking complete.",
            }
        )
        return {
            "retrieved_docs": reranked_docs,
            "doc_relevance_scores": doc_relevance_scores,
        }
    except Exception as e:
        logger.exception(f"Error in rerank_docs_node: {e}")
        stream_writer(
            {
                "type": "Rerank Docs",
                "message": "An error occurred during reranking. Returning original retrieved documents.",
            }
        )
        return {
            "retrieved_docs": state["retrieved_docs"][: state["top_k"]],
            "doc_relevance_scores": [1.0]
            * min(state["top_k"], len(state["retrieved_docs"])),
        }
