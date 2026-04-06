"""
Utility functions for generating slugs from names and names from slugs.
"""

import re
import unicodedata


def generate_name_from_slug(slug: str) -> str:
    """
    Generate a human-readable name from a slug.

    Examples:
        - "llama-3.3-70b-versatile" -> "Llama 3.3 70B Versatile"
        - "openai/gpt-oss-20b" -> "GPT OSS 20B"
        - "nvidia/nemotron-3-super-120b-a12b:free" -> "Nemotron 3 Super 120B A12B"
        - "gpt-4-turbo" -> "GPT 4 Turbo"

    Args:
        slug: The slug to convert to a name

    Returns:
        A human-readable name
    """
    # Remove service prefix if present (anything before /)
    if "/" in slug:
        slug = slug.split("/")[-1]

    # Remove suffix after colon (e.g., :free)
    if ":" in slug:
        slug = slug.split(":")[0]

    # Replace hyphens and underscores with spaces
    name = slug.replace("-", " ").replace("_", " ")

    # Split into words
    words = name.split()

    # Capitalize each word with special handling
    capitalized_words = []
    for word in words:
        # Check if word ends with 'b' and is preceded by numbers (e.g., "70b" -> "70B")
        if re.match(r"^\d+b$", word, re.IGNORECASE):
            capitalized_words.append(word.upper())
        # Check if word is all uppercase acronym-like (2-4 chars)
        elif len(word) <= 4 and word.replace(".", "").replace("-", "").isalnum():
            capitalized_words.append(word.upper())
        # Regular word capitalization
        else:
            capitalized_words.append(word.capitalize())

    return " ".join(capitalized_words)


def generate_slug(name: str) -> str:
    """
    Generate a URL-friendly slug from a name.

    Examples:
        - "GPT-4 Turbo" -> "gpt-4-turbo"
        - "Claude 3 Opus" -> "claude-3-opus"
        - "Llama 2 70B" -> "llama-2-70b"
        - "Gemini Pro 1.5" -> "gemini-pro-1-5"
        - "OpenAI Embeddings" -> "openai-embeddings"

    Args:
        name: The name to convert to a slug

    Returns:
        A URL-friendly slug
    """
    # Convert to lowercase
    slug = name.lower()

    # Remove accents and normalize unicode
    slug = unicodedata.normalize("NFKD", slug)
    slug = slug.encode("ascii", "ignore").decode("ascii")

    # Replace spaces and special characters with hyphens
    slug = re.sub(r"[^\w\s-]", "-", slug)
    slug = re.sub(r"[-\s]+", "-", slug)

    # Remove leading/trailing hyphens
    slug = slug.strip("-")

    return slug


def generate_unique_slug(name: str, existing_slugs: list[str]) -> str:
    """
    Generate a unique slug by appending a number if necessary.

    Args:
        name: The name to convert to a slug
        existing_slugs: List of existing slugs to check against

    Returns:
        A unique URL-friendly slug
    """
    base_slug = generate_slug(name)
    slug = base_slug
    counter = 1

    while slug in existing_slugs:
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug
