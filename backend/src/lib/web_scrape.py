import os
import asyncio
from typing import List

from langchain_core.documents import Document
from langchain_community.document_loaders.firecrawl import FireCrawlLoader
from firecrawl.v2.utils.error_handler import (
    WebsiteNotSupportedError,
    PaymentRequiredError,
    BadRequestError,
    UnauthorizedError,
)
from ..core.logger import SingletonLogger


class FirecrawlLoader:

    @staticmethod
    async def _load_single(url: str) -> List[Document]:
        logger = SingletonLogger().get_logger()
        loader = FireCrawlLoader(
            url=url,
            api_key=os.getenv("FIRECRAWL_API_KEY"),
            mode="scrape",
            params={"formats": ["markdown"]},
        )
        try:
            docs = await loader.aload()
            return docs or []
        except (
            WebsiteNotSupportedError,
            PaymentRequiredError,
            BadRequestError,
            UnauthorizedError,
        ):
            logger.warning(
                "Website not supported/payment required/bad request/unauthorized for URL: %s",
                url,
            )
            return [
                Document(
                    page_content="Website not supported/payment required/bad request/unauthorized",
                    metadata={"url": url},
                )
            ]
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
                    documents.extend(
                        [
                            Document(
                                page_content=doc.page_content,
                                metadata={
                                    "title": doc.metadata.get("title", ""),
                                    "description": doc.metadata.get("description", ""),
                                    "url": doc.metadata.get("url", ""),
                                    "image": doc.metadata.get("og_image", ""),
                                    "favicon": doc.metadata.get("favicon", ""),
                                    "sitename": doc.metadata.get("og:site_name", ""),
                                },
                            )
                            for doc in res
                        ]
                    )
            return documents
        except Exception:
            logger.exception("Error while loading urls with firecrawl: %s", urls)
            return []
