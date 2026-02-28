from ...embedding import EmbeddingFactory
from ...llm import LLMFactory
from ...vectorstore import VectorStoreFactory
from ....core.logger import SingletonLogger
from langchain_core.documents import Document
from ..agent_state import AgentState
from langgraph.config import get_stream_writer


async def context_retriever_node(state: AgentState):
    """Retrieves relevant context documents for a given query and paper ID."""
    logger = SingletonLogger().get_logger()
    stream_writer = get_stream_writer()
    try:
        stream_writer(
            {
                "type": "Context Retrieval",
                "message": "Retrieving relevant documents for the query...",
            }
        )
        embedding = EmbeddingFactory.build_embedding_model()
        vector_store = VectorStoreFactory.build_vector_store(embedding_model=embedding)
        retriever = vector_store.as_retriever(
            search_kwargs={
                "filter": {"paper_id": state["paper_id"]},
                "fetch_k": state["top_k"] * 5,
                "k": state["top_k"] * 2,
            },
            search_type="similarity",
        )
        relevant_docs: list[Document] = await retriever._aget_relevant_documents(
            query=state["query"], run_manager=None
        )
        stream_writer(
            {
                "type": "Context Retrieval",
                "message": f"Retrieved {len(relevant_docs)} relevant documents.",
            }
        )
        return {"retrieved_docs": relevant_docs}
    except Exception:
        logger.exception(
            "Error retrieving relevant context for query: %s", state["query"]
        )
        stream_writer(
            {
                "type": "Context Retrieval",
                "message": "An error occurred while retrieving relevant documents.",
            }
        )
        return {"retrieved_docs": []}
