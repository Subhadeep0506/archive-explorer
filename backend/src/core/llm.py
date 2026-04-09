import os
from typing import Optional, Dict
from fastapi import Request

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openrouter import ChatOpenRouter
from langchain_cohere import ChatCohere
from ..utils.api_key_utils import get_api_key_for_provider
from ..core.logger import SingletonLogger

logger = SingletonLogger().get_logger()


class LLMFactory:
    @staticmethod
    def build_llm(
        model_name: str,
        api_key: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        reasoning: str = "hidden",
        streaming: bool = False,
        request: Optional[Request] = None,
    ):
        """Build and return an LLM instance based on the provided model name and parameters.

        Args:
            model_name (str): Model name should be in `provider/model_name` format. Eg. "gemini/gemini-1.5-pro", "groq/qwen/qwen3-32b", "openrouter/nvidia/nemotron-3-nano-30b-a3b:free".
            api_key (str, optional): Explicit API key. If not provided, will fetch from request state or environment.
            max_tokens (int, optional): Maximum number of tokens to generate. Defaults to 2048.
            temperature (float, optional): Sampling temperature for generation. Defaults to 0.7.
            reasoning (str, optional): Reasoning format for the model. Defaults to "hidden".
            streaming (bool, optional): Whether to enable streaming mode. Defaults to False.
            request (Request, optional): FastAPI Request object to fetch decrypted API keys from state.

        Raises:
            ValueError: If API key is not found for the provider.
            e: If there is an error building the LLM instance.

        Returns:
            An instance of the specified LLM.
        """
        try:
            provider, model_name = model_name.split("/", 1)

            if not api_key and request:
                api_key = get_api_key_for_provider(request, provider)

            if not api_key:
                provider_names = {
                    "gemini": "Google Gemini",
                    "groq": "Groq",
                    "openrouter": "OpenRouter",
                }
                provider_display = provider_names.get(provider.lower(), provider)
                raise ValueError(
                    f"No API key found for '{provider_display}'. Please add your {provider_display} API key in Settings."
                )

            if provider.lower() == "gemini":
                llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    google_api_key=api_key,
                    include_thoughts=False,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    streaming=streaming,
                )
            elif provider.lower() == "cohere":
                llm = ChatCohere(
                    model=model_name,
                    cohere_api_key=api_key,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    streaming=streaming,
                )
            elif provider.lower() == "groq":
                reasoning_format = reasoning if "qwen" in model_name.lower() else None
                llm = ChatGroq(
                    model=model_name,
                    api_key=api_key,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    reasoning_format=reasoning_format,
                    streaming=streaming,
                )
            elif provider.lower() == "openrouter":
                llm = ChatOpenRouter(
                    model=model_name,
                    api_key=api_key,
                    temperature=temperature,
                    max_completion_tokens=max_tokens,
                    streaming=streaming,
                )
            return llm
        except Exception as e:
            logger.error(f"Error building LLM: {e}")
            raise e
