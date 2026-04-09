"""
Utility functions for API key management and extraction.
"""

from typing import Optional, Dict
from fastapi import Request


def get_api_key_for_provider(
    request: Request, provider: str, decrypted_keys: Optional[Dict[str, str]] = None
) -> Optional[str]:
    """
    Get the API key for a specific provider from decrypted keys (user settings).

    This function checks:
    1. User-provided decrypted API keys from request (if passed as parameter)
    2. Request state decrypted API keys (set by middleware)

    User-provided API keys (gemini, groq, openrouter) should ONLY come from user settings,
    not from environment variables.

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
    return None


def get_api_key_for_service(
    request: Optional[Request], service_slug: str, env_var_name: str = None
) -> Optional[str]:
    """
    Get API key for a user-provided service (embedding, web search, reranking, etc.)

    User-provided services (cohere, tavily, firecrawl, langsearch) should ONLY come from user settings,
    not from environment variables.

    Args:
        request: FastAPI Request object (can be None)
        service_slug: The service slug (e.g., 'cohere', 'tavily', 'firecrawl', 'langsearch')
        env_var_name: Deprecated - no longer used. Only user settings are checked.

    Returns:
        The API key if found, None otherwise

    Raises:
        ValueError: If the API key is not found in user settings
    """
    # Check request state (set by middleware with user's decrypted keys)
    if request and hasattr(request.state, "decrypted_api_keys"):
        api_key = request.state.decrypted_api_keys.get(service_slug)
        if api_key:
            return api_key

    # No fallback to environment variables - user must provide the key in Settings
    service_names = {
        "cohere": "Cohere",
        "tavily": "Tavily",
        "firecrawl": "Firecrawl",
        "langsearch": "LangSearch",
    }
    service_display = service_names.get(service_slug, service_slug)
    raise ValueError(
        f"No {service_display} API key found. Please add your {service_display} API key in Settings."
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
