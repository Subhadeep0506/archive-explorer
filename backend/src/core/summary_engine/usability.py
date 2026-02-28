import tiktoken

from ..vectorstore import VectorStoreFactory
from ..embedding import EmbeddingFactory
from ..llm import LLMFactory
from ...core.logger import SingletonLogger
from langchain.agents import create_agent
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from langchain_core.documents import Document
from ...lib.enum import DomainEnum, EmergingTechEnum
from ast import literal_eval

logger = SingletonLogger().get_logger()


class UsabilitySchema(BaseModel):
    """Metrics for arXiv paper usability, applicability, and reproducibility."""

    domain_applicability: Dict[DomainEnum, float] = Field(
        ..., description="Applicability scores (0.0-1.0) per domain from LLM analysis."
    )
    reproducibility_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall reproducibility (code/data/methods availability).",
    )
    new_tech_applicability: Dict[EmergingTechEnum, float] = Field(
        default_factory=dict,
        description="Scores for emerging technologies.",
    )
    impact_score: Optional[float] = Field(
        None,
        ge=0.0,
        description="Composite impact based on explained innovation over domains.",
    )


class UsabilityEngine:
    """UsabilityEngine class for generating summaries of papers."""

    @staticmethod
    async def generate_paper_summary(arxiv_id: str) -> dict:
        try:
            embedding = EmbeddingFactory.build_embedding_model()
            vector_store = VectorStoreFactory.build_vector_store(
                embedding_model=embedding
            )
            llm = LLMFactory.build_llm(
                model_name="qwen/qwen3-32b", max_tokens=4096, reasoning="hidden"
            )
            agent = create_agent(model=llm, response_format=UsabilitySchema)
            retriever = vector_store.as_retriever(
                search_kwargs={"filter": {"paper_id": arxiv_id}, "fetch_k": 9999}
            )
            docs: List[Document] = await retriever._aget_relevant_documents(
                query="*", run_manager=None
            )
            sorted_docs = await UsabilityEngine._sort_docs(docs)

            full_content = "\n\n".join([doc.page_content for doc in sorted_docs])
            final_usability_json = await UsabilityEngine.__generate_summary(
                agent, full_content
            )

            return final_usability_json
        except Exception as e:
            logger.error(
                f"Error generating usability summary for paper {arxiv_id}: {str(e)}"
            )
            raise e

    @classmethod
    async def __generate_summary(cls, agent, content: str) -> dict:
        """Generate a summary of the given content."""
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert in analyzing scientific papers. Given the content of a paper, you will evaluate its applicability across various domains, assess its reproducibility based on code/data/methods availability, and identify its relevance to emerging technologies. Provide a structured json with scores for each aspect.",
                },
                {"role": "user", "content": content},
            ]
            response = await agent.ainvoke(
                {
                    "messages": messages,
                }
            )
            return response["structured_response"].model_dump()
        except Exception as e:
            logger.error(f"Error in __generate_summary: {str(e)}")
            raise e

    @classmethod
    async def _sort_docs(cls, docs: List[Document]) -> List[Document]:
        """Sort documents by page number."""

        def extract_page_number(doc):
            try:
                return int(doc.metadata.get("page_number"))
            except (ValueError, TypeError):
                return 0

        return sorted(docs, key=extract_page_number)
