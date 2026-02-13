import os

from langchain_cohere import CohereEmbeddings


class EmbeddingFactory:
    @staticmethod
    def build_embedding_model(model_name="embed-multilingual-v3.0"):
        """Builds and returns the embedding model.
        model options: `embed-english-v3.0`, `embed-multilingual-v3.0`, `embed-v4.0`
        """
        try:
            embedding_model = CohereEmbeddings(
                model=model_name,
                cohere_api_key=os.getenv("COHERE_API_KEY"),
            )
            return embedding_model
        except Exception as e:
            print(f"Error building embedding model: {e}")
            raise e
