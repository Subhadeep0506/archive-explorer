import os
from typing import Optional
from fastapi import Request
from ..utils.api_key_utils import get_api_key_for_service
from ..core.logger import SingletonLogger
from langchain_cohere import CohereEmbeddings

logger = SingletonLogger().get_logger()


class EmbeddingFactory:
    @staticmethod
    def build_embedding_model(
        model_name="embed-multilingual-v3.0",
        api_key=None,
        request: Optional[Request] = None,
    ):
        """Builds and returns the embedding model.
        model options: `embed-english-v3.0`, `embed-multilingual-v3.0`, `embed-v4.0`

        Args:
            model_name: The embedding model name
            api_key: Explicit API key (takes precedence)
            request: FastAPI Request object to fetch API key from state
        """
        try:
            if not api_key and request:
                api_key = get_api_key_for_service(request, "cohere", "COHERE_API_KEY")

            if not api_key:
                # Fallback to environment variable
                api_key = os.getenv("COHERE_API_KEY")

            if not api_key:
                raise ValueError(
                    "No API key provided for embedding model. Please provide Cohere API key."
                )

            # Log the API key being used
            if len(api_key) > 20:
                masked_key = f"{api_key[:10]}...{api_key[-10:]}"
            else:
                masked_key = "***" + api_key[-4:] if len(api_key) > 4 else "***"
            logger.info(
                f"[Embedding Factory] Initializing Cohere embeddings with API key: {masked_key} (length: {len(api_key)})"
            )

            embedding_model = CohereEmbeddings(
                model=model_name,
                cohere_api_key=api_key,
            )
            return embedding_model
        except Exception as e:
            logger.error(f"Error initializing embedding model: {e}")
            raise e
