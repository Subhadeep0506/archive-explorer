import tiktoken
from typing import Optional
from fastapi import Request

from qdrant_client import models
from ..vectorstore import VectorStoreFactory
from ..embedding import EmbeddingFactory
from ..llm import LLMFactory
from ...core.logger import SingletonLogger
from .pdf_parser import load_pdf_content
from ...config.prompts import PAPER_SUMMARY_SYSTEM_PROMPT

logger = SingletonLogger().get_logger()


class SummaryEngine:
    """SummaryEngine class for generating summaries of papers."""

    @staticmethod
    async def generate_paper_summary(
        arxiv_id: str = None, pdf_url: str = None, request: Optional[Request] = None
    ) -> str:
        try:
            embedding = EmbeddingFactory.build_embedding_model(request=request)
            vector_store = VectorStoreFactory.build_vector_store(
                embedding_model=embedding
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
                docs = await retriever._aget_relevant_documents(
                    query="*", run_manager=None
                )
                sorted_docs = await SummaryEngine._sort_docs(docs)
                full_content = "\n\n".join([doc.page_content for doc in sorted_docs])

                if not full_content.strip() and pdf_url:
                    logger.info(
                        "No indexed content found for paper %s. Falling back to PDF URL.",
                        arxiv_id,
                    )
                    full_content = await load_pdf_content(pdf_url)
            elif pdf_url:
                full_content = await load_pdf_content(pdf_url)

            if not full_content.strip():
                raise ValueError("No paper content available for summary generation")

            encoding = tiktoken.get_encoding("cl100k_base")
            tokens = encoding.encode(full_content)
            token_limit = 32768

            cumulative_summary = ""

            if len(tokens) > token_limit:
                logger.warning(
                    f"Content for paper {arxiv_id} exceeds token limit ({len(tokens)}/{token_limit}). Generating summary in chunks."
                )
                for i in range(0, len(tokens), token_limit):
                    chunk_tokens = tokens[i : i + token_limit]
                    chunk_content = encoding.decode(chunk_tokens)
                    summary = await SummaryEngine.__generate_summary(
                        chunk_content, request
                    )
                    cumulative_summary += summary + "\n\n"
                final_summary = await SummaryEngine.__generate_summary(
                    cumulative_summary, request
                )
            else:
                final_summary = await SummaryEngine.__generate_summary(
                    full_content, request
                )
            return final_summary
        except Exception as e:
            logger.error(f"Error generating summary for paper {arxiv_id}: {str(e)}")
            raise e

    @classmethod
    async def __generate_summary(
        cls, content: str, request: Optional[Request] = None
    ) -> str:
        """Generate a summary of the given content."""
        try:
            llm = LLMFactory.build_llm(
                model_name="groq/qwen3-32b",
                max_tokens=4096,
                reasoning="hidden",
                request=request,
            )
            messages = [
                {
                    "role": "system",
                    "content": PAPER_SUMMARY_SYSTEM_PROMPT,
                },
                {"role": "user", "content": content},
            ]
            response = await llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error in __generate_summary: {str(e)}")
            raise e

    @classmethod
    async def _sort_docs(cls, docs):
        """Sort documents by page number."""

        def extract_page_number(doc):
            try:
                return int(doc.metadata.get("page_number"))
            except (ValueError, TypeError):
                return 0

        return sorted(docs, key=extract_page_number)
