import time
from typing import Any, Dict, List, Optional

import requests
import xml.etree.ElementTree as ET
from io import BytesIO
import asyncio
import fitz  # PyMuPDF
from ..core.storage import storage


class ArxivClient:
    """Lightweight client for the arXiv API with query and topic feeds.

    Features:
    - Search by free-form query (`all:` semantics)
    - Fetch feeds by user topics (OR-combined)
    - Pagination with polite rate limiting
    - Robust XML parsing for authors, links, categories, and arXiv metadata
    """

    BASE_URL = "http://export.arxiv.org/api/query"

    def __init__(
        self, wait_time_sec: float = 3.0, session: Optional[requests.Session] = None
    ):
        self.wait_time_sec = wait_time_sec
        self.session = session or requests.Session()

    def search(
        self,
        search_query: str,
        start: int = 0,
        max_results: int = 10,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        params = {
            "search_query": search_query,
            "start": start,
            "max_results": max_results,
        }
        if sort_by:
            params["sortBy"] = sort_by
        if sort_order:
            params["sortOrder"] = sort_order

        try:
            resp = self.session.get(self.BASE_URL, params=params, timeout=30)
            resp.raise_for_status()
        except requests.RequestException:
            return []

        return self._parse_response(resp.text)

    def search_paged(
        self,
        search_query: str,
        total_results: int,
        results_per_iteration: int = 50,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        all_results: List[Dict[str, Any]] = []
        for start in range(0, total_results, results_per_iteration):
            batch = self.search(
                search_query=search_query,
                start=start,
                max_results=results_per_iteration,
                sort_by=sort_by,
                sort_order=sort_order,
            )
            all_results.extend(batch)
            if start + results_per_iteration < total_results:
                time.sleep(self.wait_time_sec)
        return all_results

    def feed_by_topics(
        self,
        topics: List[str],
        start: int = 0,
        max_results: int = 10,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        cleaned = [t.strip() for t in topics if t and t.strip()]
        if not cleaned:
            return []

        topic_query = " OR ".join([f"all:{t}" for t in cleaned])
        return self.search(
            search_query=topic_query,
            start=start,
            max_results=max_results,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    def feed_by_topic_string(
        self,
        topics_csv: str,
        start: int = 0,
        max_results: int = 10,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        delimiter: str = ",",
    ) -> List[Dict[str, Any]]:
        topics = [t.strip() for t in topics_csv.split(delimiter)] if topics_csv else []
        return self.feed_by_topics(
            topics=topics,
            start=start,
            max_results=max_results,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    def _parse_response(self, response_xml: str) -> List[Dict[str, Any]]:
        try:
            root = ET.fromstring(response_xml)
        except ET.ParseError:
            return []

        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }
        results: List[Dict[str, Any]] = []

        for entry in root.findall("atom:entry", ns):
            id_text = self._text(entry.find("atom:id", ns))
            arxiv_id = id_text.split("/abs/")[-1] if id_text else None

            title = self._text(entry.find("atom:title", ns))
            summary = self._text(entry.find("atom:summary", ns))
            published = self._text(entry.find("atom:published", ns))
            updated = self._text(entry.find("atom:updated", ns))

            authors = []
            for author in entry.findall("atom:author", ns):
                name = self._text(author.find("atom:name", ns))
                aff = self._text(author.find("arxiv:affiliation", ns))
                authors.append(name if not aff else f"{name} ({aff})")

            pdf_url: Optional[str] = None
            paper_url: Optional[str] = None
            for link in entry.findall("atom:link", ns):
                rel = link.get("rel")
                href = link.get("href")
                title_attr = link.get("title")
                if title_attr == "pdf":
                    pdf_url = href
                elif rel == "alternate":
                    paper_url = href

            categories = [
                c.get("term")
                for c in entry.findall("atom:category", ns)
                if c.get("term")
            ]
            primary_cat_elem = entry.find("arxiv:primary_category", ns)
            primary_category = (
                primary_cat_elem.get("term") if primary_cat_elem is not None else None
            )

            comment = self._text(entry.find("arxiv:comment", ns))
            journal_ref = self._text(entry.find("arxiv:journal_ref", ns))
            doi = self._text(entry.find("arxiv:doi", ns))

            results.append(
                {
                    "id": id_text,
                    "arxiv_id": arxiv_id,
                    "title": title,
                    "abstract": summary,
                    "authors": authors,
                    "pdf_url": pdf_url,
                    "paper_url": paper_url,
                    "categories": categories,
                    "primary_category": primary_category,
                    "published": published,
                    "updated": updated,
                    "comment": comment,
                    "journal_ref": journal_ref,
                    "doi": doi,
                }
            )

        return results

    @staticmethod
    def _text(elem: Optional[ET.Element]) -> Optional[str]:
        return elem.text.strip() if elem is not None and elem.text else None


async def generate_first_page_thumbnail(
    pdf_url: str,
    user_id: int,
    target_width: int = 400,
    folder: str = "thumbnails",
) -> Optional[str]:
    """Render the first page of the given PDF URL to a PNG and upload it.

    Returns the public URL, or None on failure.
    """
    if not pdf_url:
        return None

    try:
        resp = requests.get(pdf_url, timeout=60)
        resp.raise_for_status()
        pdf_bytes = resp.content
    except requests.RequestException:
        return None

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if doc.page_count == 0:
            return None
        page = doc.load_page(0)

        # Compute scale to approximate target width
        page_width_pts = page.rect.width  # points at 72 dpi
        scale = max(0.5, min(6.0, target_width / max(1.0, page_width_pts)))
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        buf = BytesIO()
        pix.save(buf, format="PNG")
        image_bytes = buf.getvalue()
        buf.close()
    except Exception:
        return None

    try:
        filename = pdf_url.split("/")[-1] + ".png"
        key = await storage.upload_bytes(
            content=image_bytes,
            user_id=user_id,
            folder=folder,
            filename=filename,
            content_type="image/png",
        )
        return storage.get_file_url(key)
    except Exception:
        return None
