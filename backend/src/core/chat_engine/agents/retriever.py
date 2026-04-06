import math

from ...embedding import EmbeddingFactory
from ....controller.message import get_messages_by_session
from ...vectorstore import VectorStoreFactory
from ....core.logger import SingletonLogger
from langchain_core.documents import Document
from ..agent_state import AgentState
from langgraph.config import get_stream_writer


def extract_paper_meta_from_docs(docs: list[Document]) -> str:
    """Extracts the paper metadata from a list of documents."""
    title, author = "Unknown Title", "Unknown Author"
    for doc in docs:
        if "title" in doc.metadata:
            title = doc.metadata["title"]
        if "author" in doc.metadata:
            author = doc.metadata["author"]
    return title, author


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
        embedding = EmbeddingFactory.build_embedding_model(request=state.get("request"))
        vector_store = VectorStoreFactory.build_vector_store(embedding_model=embedding)
        retriever = vector_store.as_retriever(
            search_kwargs={
                "filter": {"paper_id": state["paper_id"]},
                "fetch_k": state["top_k"] * 2,
                "k": (
                    math.ceil(
                        state["top_k"] * 0.4
                    )  # Adjusted to 40% of top_k for vector store results if web search is used
                    if state["use_web_search"]
                    else state["top_k"]
                ),
            },
            search_type="similarity",
        )
        relevant_docs: list[Document] = await retriever._aget_relevant_documents(
            query=state["query"], run_manager=None
        )
        title, author = extract_paper_meta_from_docs(relevant_docs)

        conversation_history = await get_messages_by_session(
            session_id=state["conversation_id"], user_id=state["user_id"]
        )

        stream_writer(
            {
                "type": "Context Retrieval",
                "message": f"Retrieved {len(relevant_docs)} relevant documents.",
            }
        )
        return {
            "retrieved_docs": relevant_docs,
            "paper_title": title,
            "paper_authors": author,
            "messages": conversation_history,
        }
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
        return {
            "retrieved_docs": [],
            "paper_title": "Unknown Title",
            "paper_authors": "Unknown Author",
        }
