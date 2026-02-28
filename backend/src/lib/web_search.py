import asyncio
import os
from typing import List, Dict

from langchain_tavily import TavilySearch
from ..core.logger import SingletonLogger


class TavilyWebSearch:
    """Wrapper for Tavily search (langchain_tavily)."""

    @staticmethod
    async def search(
        query: str, num: int = 10, topic: str = "general"
    ) -> List[Dict[str, str]]:
        tavily_api_key = os.getenv("TAVILY_SEARCH_API_KEY")
        logger = SingletonLogger().get_logger()

        def _call():
            search = TavilySearch(tavily_api_key=tavily_api_key, topic=topic)
            return search.run(query, num_results=min(max(1, num), 50))

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
