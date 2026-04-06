"""
Utility functions for API key management and extraction.
"""

import os
from typing import Optional, Dict
from fastapi import Request


def get_api_key_for_provider(
    request: Request, provider: str, decrypted_keys: Optional[Dict[str, str]] = None
) -> Optional[str]:
    """
    Get the API key for a specific provider from decrypted keys or environment variables.

    This function checks:
    1. User-provided decrypted API keys from request (if passed as parameter)
    2. Request state decrypted API keys (set by middleware)
    3. Environment variables as fallback

    Args:
        request: FastAPI Request object
        provider: The provider name (e.g., 'gemini', 'groq', 'openrouter')
        decrypted_keys: Optional dictionary of decrypted keys (overrides request.state)

    Returns:
        The API key for the provider, or None if not found
    """
    # Provider slug mapping to handle variations
    provider_slug_map = {
        "gemini": ["gemini", "google", "google-generativeai"],
        "groq": ["groq"],
        "openrouter": ["openrouter"],
    }
    provider = provider.lower()
    possible_slugs = provider_slug_map.get(provider, [provider])

    if decrypted_keys:
        for slug in possible_slugs:
            if slug in decrypted_keys:
                return decrypted_keys[slug]

    if hasattr(request.state, "decrypted_api_keys"):
        for slug in possible_slugs:
            if slug in request.state.decrypted_api_keys:
                api_key = request.state.decrypted_api_keys[slug]
                return api_key
    else:
        raise ValueError(
            "request.state.decrypted_api_keys is not set. Ensure APIKeyDecryptionMiddleware is properly configured."
        )
    env_var_map = {
        "gemini": "GOOGLE_API_KEY",
        "groq": "GROQ_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }
    env_var = env_var_map.get(provider)
    if env_var:
        api_key = os.getenv(env_var)
        if api_key:
            return api_key
    return None


def get_api_key_for_service(
    request: Optional[Request], service_slug: str, env_var_name: str
) -> Optional[str]:
    """
    Get API key for a service (embedding, web search, reranking, etc.)

    Args:
        request: FastAPI Request object (can be None)
        service_slug: The service slug (e.g., 'cohere', 'tavily', 'firecrawl', 'langsearch')
        env_var_name: Environment variable name to fall back to

    Returns:
        The API key if found, None otherwise
    """
    # 1. Check request state (set by middleware)
    if request and hasattr(request.state, "decrypted_api_keys"):
        api_key = request.state.decrypted_api_keys.get(service_slug)
        if api_key:
            return api_key

    api_key = os.getenv(env_var_name)
    if api_key:
        return api_key
    raise ValueError(
        f"No API key found for service '{service_slug}'. Ensure it is set in request.state.decrypted_api_keys or environment variable '{env_var_name}'."
    )


def extract_decrypted_keys_dict(api_keys_encrypted: Optional[list]) -> Dict[str, str]:
    """
    Extract decrypted API keys from a list of encrypted API key items.

    Note: This function expects the keys to already be decrypted by the middleware.
    It simply converts the list format to a dictionary format.

    Args:
        api_keys_encrypted: List of API key items (already decrypted by middleware)

    Returns:
        Dictionary mapping service slug to API key
    """
    if not api_keys_encrypted:
        return {}

    decrypted_keys = {}
    for item in api_keys_encrypted:
        if isinstance(item, dict):
            slug = item.get("slug")
            api_key = item.get("api_key")
            if slug and api_key:
                decrypted_keys[slug] = api_key

    return decrypted_keys
