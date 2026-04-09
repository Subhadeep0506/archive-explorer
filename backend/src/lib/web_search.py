import asyncio
from typing import List, Dict, Optional
from fastapi import Request

from langchain_tavily import TavilySearch
from ..core.logger import SingletonLogger
from ..utils.api_key_utils import get_api_key_for_service


class TavilyWebSearch:
    """Wrapper for Tavily search (langchain_tavily)."""

    @staticmethod
    async def search(
        query: str,
        num: int = 10,
        topic: str = "general",
        api_key: Optional[str] = None,
        request: Optional[Request] = None,
    ) -> List[Dict[str, str]]:
        if not api_key and request:
            api_key = get_api_key_for_service(request, "tavily")

        tavily_api_key = api_key
        logger = SingletonLogger().get_logger()

        def _call():
            search = TavilySearch(tavily_api_key=tavily_api_key, topic=topic)
            return search.run(query, num_results=num // 2)

        loop = asyncio.get_event_loop()
        try:
            raw = await loop.run_in_executor(None, _call)
        except Exception as e:
            logger.exception("Error calling Tavily search: %s", e)
            return []

        results: List[Dict[str, str]] = []
        for item in raw.get("results", []) if isinstance(raw, dict) else []:
            try:
                title = item.get("title") or "(no title)"
                url = item.get("link") or item.get("url") or "(no url)"
                snippet = item.get("content") or item.get("snippet") or "(no snippet)"
                results.append({"title": title, "url": url, "snippet": snippet})
            except Exception:
                logger.exception("Error parsing Tavily result: %s", item)

        return results
