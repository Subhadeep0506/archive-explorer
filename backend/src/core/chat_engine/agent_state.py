from typing import List, TypedDict, Dict, Optional, Any
from typing_extensions import NotRequired
from langchain_core.documents import Document


class AgentState(TypedDict):
    """Represents the state of an agent in a conversation."""

    conversation_id: str
    paper_id: str
    paper_title: str
    paper_authors: str
    user_id: str
    messages: List[dict]
    query: str
    model_name: str
    top_k: int
    temperature: float
    max_tokens: int
    use_web_search: NotRequired[bool]
    web_search_topic: NotRequired[str]
    retrieved_docs: List[Document]
    doc_relevance_scores: List[float]
    web_search_results: List[Document]
    response: str
    response_metadata: Dict
    request: NotRequired[Optional[Any]]
