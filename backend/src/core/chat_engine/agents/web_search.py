from ....lib.web_search import TavilyWebSearch

# from ....lib.langsearch import LangSearchClient
from ....core.logger import SingletonLogger
from typing import List


async def web_search_node(
    query: str, num: int = 10, topic: str = "general", request=None
) -> List[dict]:
    """Perform a web search using Tavily and return the results.
    Returns a list of dictionaries with 'title', 'url', and 'snippet' keys.
    """
    logger = SingletonLogger().get_logger()
    logger.info(
        f"Performing web search for query: {query} with num: {num} and topic: {topic}"
    )
    try:
        results = await TavilyWebSearch.search(
            query=query, num=num, topic=topic, request=request
        )
        return results
    except Exception as e:
        logger.exception(f"Error during web search: {e}")
        return []
