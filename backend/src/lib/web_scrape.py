import asyncio
from typing import List, Optional
from fastapi import Request

from langchain_core.documents import Document
from langchain_community.document_loaders.firecrawl import (
    FireCrawlLoader as BasFireCrawlLoader,
)
from firecrawl.v2.utils.error_handler import (
    WebsiteNotSupportedError,
    PaymentRequiredError,
    BadRequestError,
    UnauthorizedError,
)
from ..core.logger import SingletonLogger
from ..utils.api_key_utils import get_api_key_for_service


class FirecrawlLoader:

    @staticmethod
    async def _load_single(url: str, api_key: str) -> List[Document]:
        logger = SingletonLogger().get_logger()
        loader = BasFireCrawlLoader(
            url=url,
            api_key=api_key,
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
    async def scrape(
        urls: List[str],
        api_key: Optional[str] = None,
        request: Optional[Request] = None,
    ) -> List[Document]:
        logger = SingletonLogger().get_logger()
        try:
            if not api_key and request:
                api_key = get_api_key_for_service(request, "firecrawl")

            if not urls:
                return []
            if isinstance(urls, str):
                urls = [urls]
            tasks = [FirecrawlLoader._load_single(url, api_key) for url in urls]
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
