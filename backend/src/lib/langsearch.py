import os
import requests
import json
from typing import Dict
from langchain_core.documents import Document
from ..core.logger import SingletonLogger

RERANK_BASE_URL = "https://api.langsearch.com/v1/rerank"
SEARCH_BASE_URL = "https://api.langsearch.com/v1/web-search"
logger = SingletonLogger().get_logger()


class LangSearchClient:
    @staticmethod
    async def rerank_docs(
        query: str, documents: list[Document], top_n: int = 5
    ) -> list[Document]:
        # Validate inputs
        if not documents:
            logger.warning("No documents to rerank")
            return [], []

        if not query or not query.strip():
            logger.warning("Empty query provided for reranking")
            return documents[:top_n], [1.0] * min(top_n, len(documents))

        # Extract page content and filter empty docs
        doc_contents = []
        valid_doc_indices = []
        for idx, doc in enumerate(documents):
            content = (
                doc.page_content.strip()
                if hasattr(doc, "page_content")
                else str(doc).strip()
            )
            if content:
                doc_contents.append(content)
                valid_doc_indices.append(idx)

        if not doc_contents:
            logger.warning("All documents have empty content")
            return [], []

        payload = json.dumps(
            {
                "model": "langsearch-reranker-v1",
                "query": query,
                "top_n": min(top_n, len(doc_contents)),
                "return_documents": False,
                "documents": doc_contents,
            }
        )
        headers = {
            "Authorization": f'Bearer {os.getenv("LANGSEARCH_API_KEY")}',
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(RERANK_BASE_URL, headers=headers, data=payload)
            response.raise_for_status()
            result = response.json()

            # Map back to original document indices
            reranked_docs = []
            relevance_scores = []
            for doc in result["results"]:
                original_idx = valid_doc_indices[doc["index"]]
                reranked_docs.append(documents[original_idx])
                relevance_scores.append(doc["relevance_score"])

            return reranked_docs, relevance_scores
        except requests.RequestException as e:
            logger.error(f"Error reranking documents: {e}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.error(f"API error details: {error_detail}")
                except:
                    logger.error(f"API response text: {e.response.text}")
            return documents[:top_n], [1.0] * min(top_n, len(documents))

    @staticmethod
    async def search(
        query: str, num: int = 10, freshness: str = "noLimit"
    ) -> list[Dict[str, str]]:
        """
        Perform a web search using LangSearch API.

        Args:
            query (str): The search query.
            num (int, optional): The number of results to return. Defaults to 10.
            freshness (str, optional): The freshness filter for search results. Defaults to "noLimit". Options include "oneDay", "oneWeek", "oneMonth", "oneYear", and "noLimit".

        Returns:
            list[Dict[str, str]]: A list of dictionaries representing the search results.
        """
        payload = json.dumps(
            {
                "query": query,
                "freshness": freshness,
                "count": num,
            }
        )
        headers = {
            "Authorization": f'Bearer {os.getenv("LANGSEARCH_API_KEY")}',
            "Content-Type": "application/json",
        }
        try:
            response = requests.request(
                "POST", SEARCH_BASE_URL, headers=headers, data=payload
            )
            response.raise_for_status()
            result = response.json()
            web_pages = result.get("data", {}).get("webPages", {}).get("value", [])
            documents = [
                {
                    "title": page.get("name", ""),
                    "url": page.get("url", ""),
                    "snippet": page.get("snippet", ""),
                }
                for page in web_pages
            ]
            return documents
        except requests.RequestException as e:
            logger.error(f"Error performing web search: {e}")
            return []
