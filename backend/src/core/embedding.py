import os
from typing import Optional
from fastapi import Request
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
            # Get API key from request state (set by load_user_api_keys dependency)
            if not api_key and request:
                if hasattr(request.state, "decrypted_api_keys"):
                    api_key = request.state.decrypted_api_keys.get("cohere")

            if not api_key:
                raise ValueError(
                    "No Cohere API key found. Please add your Cohere API key in Settings."
                )

            embedding_model = CohereEmbeddings(
                model=model_name,
                cohere_api_key=api_key,
            )
            return embedding_model
        except Exception as e:
            logger.error(f"Error initializing embedding model: {e}")
            raise e
