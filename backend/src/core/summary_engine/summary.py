import tiktoken

from ..vectorstore import VectorStoreFactory
from ..embedding import EmbeddingFactory
from ..llm import LLMFactory
from ...core.logger import SingletonLogger

logger = SingletonLogger().get_logger()


class SummaryEngine:
    """SummaryEngine class for generating summaries of papers."""

    @staticmethod
    async def generate_paper_summary(arxiv_id: str) -> str:
        try:
            embedding = EmbeddingFactory.build_embedding_model()
            vector_store = VectorStoreFactory.build_vector_store(
                embedding_model=embedding
            )
            retriever = vector_store.as_retriever(
                search_kwargs={"filter": {"paper_id": arxiv_id}, "fetch_k": 9999}
            )
            docs = await retriever._aget_relevant_documents(query="*", run_manager=None)
            sorted_docs = await SummaryEngine._sort_docs(docs)

            full_content = "\n\n".join([doc.page_content for doc in sorted_docs])
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
                    summary = await SummaryEngine.__generate_summary(chunk_content)
                    cumulative_summary += summary + "\n\n"
                final_summary = await SummaryEngine.__generate_summary(
                    cumulative_summary
                )
            else:
                final_summary = await SummaryEngine.__generate_summary(full_content)
            return final_summary
        except Exception as e:
            logger.error(f"Error generating summary for paper {arxiv_id}: {str(e)}")
            raise e

    @classmethod
    async def __generate_summary(cls, content: str) -> str:
        """Generate a summary of the given content."""
        try:
            llm = LLMFactory.build_llm(
                model_name="qwen/qwen3-32b", max_tokens=4096, reasoning="hidden"
            )
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes academic papers. Generate a comprehensive summary of the following arxiv article content, ensuring to capture the key points, innovations, methodologies, and findings. Include key metrics, results, and any significant conclusions. Make the summary concise yet informative, suitable for a researcher looking to quickly understand the essence of the paper. Start directly with a short summary of the abstract, followed by a more detailed summary of the main content, with titles as mentioned above. Do not start with 'Summary of ...' and other similar phrases. Just provide the summary in a clear and structured manner.",
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
