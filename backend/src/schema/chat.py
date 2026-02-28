from pydantic import BaseModel, Field
from typing import Optional


class ChatQueryRequest(BaseModel):
    """Request model for chat queries."""

    query: str = Field(..., description="The user's question or query")
    paper_id: str = Field(..., description="The paper ID to query against")
    session_id: int = Field(
        ..., description="The session/thread ID for conversation history"
    )
    model_name: str = Field(default="gpt-4o-mini", description="The LLM model to use")
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Model temperature"
    )
    max_tokens: int = Field(
        default=2048, ge=1, le=8192, description="Maximum tokens to generate"
    )
    top_k: int = Field(
        default=5, ge=1, le=20, description="Number of documents to retrieve"
    )
    use_web_search: bool = Field(default=False, description="Whether to use web search")
    web_search_topic: str = Field(default="general", description="Topic for web search")


class ChatQueryResponse(BaseModel):
    """Response model for chat queries."""

    session_id: int
    query: str
    response: str
    model_used: str
    tokens_used: Optional[dict] = None

    class Config:
        from_attributes = True
