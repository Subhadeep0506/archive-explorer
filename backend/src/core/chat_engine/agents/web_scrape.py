from ....lib.web_scrape import FirecrawlLoader
from ....core.logger import SingletonLogger
from typing import List
from .web_search import web_search_node
from ..agent_state import AgentState
from langgraph.config import get_stream_writer


async def web_crawl_node(state: AgentState):
    """Perform a web crawl using Tavily and return the results.
    Returns a list of dictionaries with 'title', 'url', and 'snippet' keys.
    """
    logger = SingletonLogger().get_logger()
    logger.info(
        f"Performing web crawl for query: {state['query']} with num: {state['top_k']} and topic: {state['web_search_topic']}"
    )
    stream_writer = get_stream_writer()
    try:
        stream_writer(
            {
                "type": "Web Crawl",
                "message": f"Performing web search for query: {state['query']}...",
            }
        )
        search_results = await web_search_node(
            query=state["query"], num=state["top_k"], topic=state["web_search_topic"]
        )
        stream_writer(
            {
                "type": "Web Crawl",
                "message": f"Web search complete. Found {len(search_results)} results. Starting web crawl...",
            }
        )
        results = await FirecrawlLoader.scrape(
            urls=[item["url"] for item in search_results]
        )
        stream_writer(
            {
                "type": "Web Crawl",
                "message": f"Web crawl complete. Scraped {len(results)} results.",
            }
        )
        return {"web_search_results": results}
    except Exception as e:
        logger.exception(f"Error during web crawl: {e}")
        stream_writer(
            {
                "type": "Web Crawl",
                "message": "An error occurred during the web crawl.",
            }
        )
        return []
