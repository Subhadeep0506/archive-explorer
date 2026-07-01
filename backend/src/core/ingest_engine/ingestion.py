import asyncio

from qdrant_client import models
from ..embedding import EmbeddingFactory
from ..vectorstore import VectorStoreFactory
from langchain_text_splitters import CharacterTextSplitter
from langchain_pymupdf4llm import PyMuPDF4LLMLoader
from typing import List, Optional
from fastapi import Request
from ...lib.qdrant import get_qdrant_client, CHUNKS_COLLECTION
from ...core.logger import SingletonLogger

logger = SingletonLogger().get_logger()


class IngestionEngine:
    @staticmethod
    async def ingest_paper_using_paper_id(
        paper_id: str, paper_url: str, embedding_model: str = "embed-multilingual-v3.0", request: Optional[Request] = None
    ):
        try:
            embedding = EmbeddingFactory.build_embedding_model(embedding_model, request=request)
            vector_store = VectorStoreFactory.build_vector_store(
                embedding_model=embedding
            )
            loader = PyMuPDF4LLMLoader(
                file_path=paper_url,
            )
            text_splitter = CharacterTextSplitter(chunk_size=2000, chunk_overlap=500, separator="\n")
            documents = []
            async for doc in loader.alazy_load():
                doc.metadata["paper_id"] = paper_id
                documents.append(doc)

            documents = text_splitter.split_documents(documents)
            _ = await vector_store.aadd_documents(documents)
        except Exception as e:
            logger.error(f"Error ingesting paper: {e}")
            raise e

    @staticmethod
    async def delete_paper_using_paper_ids(paper_ids: List[str], request: Optional[Request] = None):
        try:
            client = get_qdrant_client()
            filter_condition = models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.paper_id",
                        match=models.MatchAny(any=paper_ids),
                    )
                ]
            )
            await asyncio.to_thread(
                client.delete,
                collection_name=CHUNKS_COLLECTION,
                points_selector=models.FilterSelector(filter=filter_condition),
            )
        except Exception as e:
            logger.error(f"Error deleting paper: {e}")
            raise e
