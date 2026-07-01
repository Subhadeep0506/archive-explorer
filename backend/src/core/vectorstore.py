from langchain_qdrant import QdrantVectorStore
from ..lib.qdrant import get_qdrant_client, CHUNKS_COLLECTION
from ..core.logger import SingletonLogger

logger = SingletonLogger().get_logger()


class VectorStoreFactory:
    @staticmethod
    def build_vector_store(embedding_model) -> QdrantVectorStore:
        try:
            return QdrantVectorStore(
                client=get_qdrant_client(),
                collection_name=CHUNKS_COLLECTION,
                embedding=embedding_model,
            )
        except Exception as e:
            logger.error(f"Error building vector store: {e}")
            raise e
