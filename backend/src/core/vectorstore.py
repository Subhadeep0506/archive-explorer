import os

from langchain_pinecone import PineconeVectorStore
from ..core.logger import SingletonLogger

logger = SingletonLogger().get_logger()


class VectorStoreFactory:
    @staticmethod
    def build_vector_store(
        embedding_model, index_name="arxiv-app"
    ) -> PineconeVectorStore:
        """Builds and returns the vector store."""
        try:
            vector_store = PineconeVectorStore(
                embedding=embedding_model,
                index_name=index_name,
                namespace="papers",
                pinecone_api_key=os.getenv("PINECONE_API_KEY"),
                host=os.getenv("PINECONE_URI"),
            )
            return vector_store
        except Exception as e:
            logger.error(f"Error building vector store: {e}")
            raise e
