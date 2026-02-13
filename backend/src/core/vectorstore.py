import os

from langchain_pinecone import PineconeVectorStore


class VectorStoreFactory:
    @staticmethod
    def build_vector_store(embedding_model, index_name="arxiv-app") -> PineconeVectorStore:
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
            print(f"Error building vector store: {e}")
            raise e
