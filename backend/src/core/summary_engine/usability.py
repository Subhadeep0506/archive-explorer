import tiktoken
from typing import Optional
from fastapi import Request

from langchain.agents import create_agent
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from qdrant_client import models
from langchain_core.documents import Document
from ..vectorstore import VectorStoreFactory
from ..embedding import EmbeddingFactory
from ..llm import LLMFactory
from ...core.logger import SingletonLogger
from ...lib.enum import DomainEnum, EmergingTechEnum, ReproducibilityEnum
from ...config.prompts import USABILITY_GENERATION_SYSTEM_PROMPT
from .pdf_parser import load_pdf_content

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


class UsabilityEngine:
    """UsabilityEngine class for generating summaries of papers."""

    DEFAULT_MODEL = "groq/qwen3-32b"

    @staticmethod
    async def generate_paper_summary(
        arxiv_id: str = None, pdf_url: str = None, request: Optional[Request] = None,
        model_name: Optional[str] = None,
    ) -> dict:
        """Generate a summary of the paper's usability, applicability, and reproducibility based on its content.

        Args:
            arxiv_id (str, optional): arXiv ID of the paper. Defaults to None.
            pdf_url (str, optional): URL of the PDF. Defaults to None.
            request (Request, optional): FastAPI Request object to fetch API keys. Defaults to None.

        Raises:
            NotImplementedError: If PDF URL processing is not implemented.
            e: If any other error occurs.

        Returns:
            dict: A dictionary containing the usability summary with keys 'domain_applicability', 'reproducibility_score', 'new_tech_applicability', and 'impact_score'.
        """
        try:
            embedding = EmbeddingFactory.build_embedding_model(request=request)
            vector_store = VectorStoreFactory.build_vector_store(
                embedding_model=embedding
            )
            llm = LLMFactory.build_llm(
                model_name=model_name or UsabilityEngine.DEFAULT_MODEL,
                max_tokens=4096,
                reasoning="hidden",
                request=request,
            )
            agent = create_agent(
                system_prompt=USABILITY_GENERATION_SYSTEM_PROMPT,
                model=llm,
                response_format=UsabilitySchema,
            )
            full_content = ""

            if arxiv_id:
                filter_condition = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="metadata.paper_id",
                            match=models.MatchValue(value=arxiv_id),
                        )
                    ]
                )
                retriever = vector_store.as_retriever(
                    search_kwargs={"filter": filter_condition, "k": 200}
                )
                docs: List[Document] = await retriever._aget_relevant_documents(
                    query="*", run_manager=None
                )
                sorted_docs = await UsabilityEngine._sort_docs(docs)
                full_content = "\n\n".join([doc.page_content for doc in sorted_docs])

                if not full_content.strip() and pdf_url:
                    logger.info(
                        "No indexed content found for paper %s usability. Falling back to PDF URL.",
                        arxiv_id,
                    )
                    full_content = await load_pdf_content(pdf_url)
            elif pdf_url:
                full_content = await load_pdf_content(pdf_url)

            if not full_content.strip():
                raise ValueError("No paper content available for usability generation")

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
