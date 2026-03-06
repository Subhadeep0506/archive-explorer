import tiktoken

from ..vectorstore import VectorStoreFactory
from ..embedding import EmbeddingFactory
from ..llm import LLMFactory
from ...core.logger import SingletonLogger
from langchain.agents import create_agent
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from langchain_core.documents import Document
from ...lib.enum import DomainEnum, EmergingTechEnum, ReproducibilityEnum
from .pdf_parser import load_pdf_content
from ast import literal_eval

logger = SingletonLogger().get_logger()


class UsabilitySchema(BaseModel):
    """Metrics for arXiv paper usability, applicability, and reproducibility."""

    domain_applicability: Dict[DomainEnum, float] = Field(
        ...,
        description="Applicability scores (0.0-1.0) per domain based on LLM analysis. Give detailed scores for each domain with dense values.",
    )
    reproducibility_score: Dict[ReproducibilityEnum, float] = Field(
        ...,
        description="Scores (0.0-1.0) for reproducibility and reapplicability based on code/data/methods availability. Provide separate scores for both Reproducible and Reapplicable aspects. Give detailed scores with dense values. E.g {'Reproducible': 0.65, 'Reapplicable': 0.72}",
    )
    new_tech_applicability: Dict[EmergingTechEnum, float] = Field(
        default_factory=dict,
        description="Scores for emerging technologies. All technologies should be included with a score of 0.0 if not applicable. Give detailed scores for each domain with dense values. E.g 0.46",
    )
    impact_score: float = Field(
        default=0.0,
        ge=0.0,
        description="Composite impact based on explained innovation over domains. Give detailed overall score with dense value. E.g 0.83",
    )


SYSTEM_PROMPT = """You are an expert in analyzing scientific papers. Given the content of a paper, you will evaluate its applicability across various domains, assess its reproducibility based on code/data/methods availability, and identify its relevance to emerging technologies.

IMPORTANT: Use ONLY these exact keys (case-sensitive):

domain_applicability - Use ONLY these business/industry domains:
Marketing, Finance, Legal, Insurance, Technology, Industrial, Healthcare, Education, Automobile, Agriculture, Telecommunications, Manufacturing, Media

reproducibility_score - Use ONLY these two keys:
Reproducible, Reapplicable

new_tech_applicability - Use ONLY these emerging technology areas:
Machine Learning, Deep Learning, Computer Vision, Natural Language Processing, LLMs, VLMs, RAG, Agentic AI, Multimodal AI, Cloud Computing, Observability, Cybersecurity, Reinforcement Learning, Robotics

Provide scores (0.0-1.0) for ALL items in each category. Scores must be dense and varied based on the content (e.g., 0.43, 0.67, 0.82), not just 0.9 or 0.1. Use 0.0 for non-applicable items. Be detailed in your analysis and provide nuanced scores that reflect the paper's strengths and weaknesses across different areas.
"""


class UsabilityEngine:
    """UsabilityEngine class for generating summaries of papers."""

    @staticmethod
    async def generate_paper_summary(arxiv_id: str = None, pdf_url: str = None) -> dict:
        """Generate a summary of the paper's usability, applicability, and reproducibility based on its content.

        Args:
            arxiv_id (str, optional): arXiv ID of the paper. Defaults to None.
            pdf_url (str, optional): URL of the PDF. Defaults to None.

        Raises:
            NotImplementedError: If PDF URL processing is not implemented.
            e: If any other error occurs.

        Returns:
            dict: A dictionary containing the usability summary with keys 'domain_applicability', 'reproducibility_score', 'new_tech_applicability', and 'impact_score'.
        """
        try:
            embedding = EmbeddingFactory.build_embedding_model()
            vector_store = VectorStoreFactory.build_vector_store(
                embedding_model=embedding
            )
            llm = LLMFactory.build_llm(
                model_name="qwen/qwen3-32b", max_tokens=4096, reasoning="hidden"
            )
            agent = create_agent(
                system_prompt=SYSTEM_PROMPT, model=llm, response_format=UsabilitySchema
            )
            if arxiv_id:
                retriever = vector_store.as_retriever(
                    search_kwargs={"filter": {"paper_id": arxiv_id}, "fetch_k": 9999}
                )
                docs: List[Document] = await retriever._aget_relevant_documents(
                    query="*", run_manager=None
                )
                sorted_docs = await UsabilityEngine._sort_docs(docs)
                full_content = "\n\n".join([doc.page_content for doc in sorted_docs])
            elif pdf_url:
                full_content = await load_pdf_content(pdf_url)

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
