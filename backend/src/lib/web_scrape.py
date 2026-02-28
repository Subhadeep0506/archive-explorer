import os
import asyncio
from typing import List

from langchain_core.documents import Document
from langchain_community.document_loaders.firecrawl import FireCrawlLoader
from ..core.logger import SingletonLogger


class FirecrawlLoader:

    @staticmethod
    async def _load_single(url: str) -> List[Document]:
        logger = SingletonLogger().get_logger()
        loader = FireCrawlLoader(
            url=url,
            api_key=os.getenv("FIRECRAWL_API_KEY"),
            mode="scrape",
        )
        try:
            docs = await loader.aload()
            return docs or []
        except Exception:
            logger.exception("Error while loading url with firecrawl: %s", url)
            return []

    @staticmethod
    async def scrape(urls: List[str]) -> List[Document]:
        logger = SingletonLogger().get_logger()
        try:
            if not urls:
                return []
            if isinstance(urls, str):
                urls = [urls]
            tasks = [FirecrawlLoader._load_single(url) for url in urls]
            results = await asyncio.gather(*tasks)
            documents: List[Document] = []
            for res in results:
                if res:
                    documents.extend(res)
            return documents
        except Exception:
            logger.exception("Error while loading urls with firecrawl: %s", urls)
            return []
