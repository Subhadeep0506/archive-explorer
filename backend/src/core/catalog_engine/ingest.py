import asyncio
import uuid
import xml.etree.ElementTree as ET
from typing import Optional

from sickle import Sickle
from sickle.models import Record
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from qdrant_client.http.models import PointStruct, Document

from ...model.arxiv_catalog import ArxivCatalog
from ...lib.qdrant import get_qdrant_client, CATALOG_COLLECTION, CATALOG_EMBED_MODEL
from ...core.logger import SingletonLogger

logger = SingletonLogger().get_logger()

OAI_ENDPOINT = "http://export.arxiv.org/oai2"
ARXIV_NS = "http://arxiv.org/OAI/arXiv/"


def _parse_arxiv_record(record: Record) -> Optional[dict]:
    if record.deleted:
        return None

    try:
        meta = record.xml.find(f".//{{{ARXIV_NS}}}arXiv")
        if meta is None:
            return None

        arxiv_id = (meta.findtext(f"{{{ARXIV_NS}}}id") or "").strip()
        if not arxiv_id:
            return None

        title = (meta.findtext(f"{{{ARXIV_NS}}}title") or "").strip()
        abstract = (meta.findtext(f"{{{ARXIV_NS}}}abstract") or "").strip()

        authors = []
        for author_el in meta.findall(f".//{{{ARXIV_NS}}}author"):
            keyname = (author_el.findtext(f"{{{ARXIV_NS}}}keyname") or "").strip()
            forenames = (author_el.findtext(f"{{{ARXIV_NS}}}forenames") or "").strip()
            if keyname:
                name = f"{forenames} {keyname}".strip()
                authors.append(name)

        categories = (meta.findtext(f"{{{ARXIV_NS}}}categories") or "").strip()
        category_list = categories.split() if categories else []
        primary_category = category_list[0] if category_list else None

        published = (meta.findtext(f"{{{ARXIV_NS}}}created") or "").strip()
        updated = (meta.findtext(f"{{{ARXIV_NS}}}updated") or "").strip()

        return {
            "arxiv_id": arxiv_id,
            "title": title,
            "abstract": abstract,
            "authors": "; ".join(authors),
            "categories": categories,
            "primary_category": primary_category,
            "published_date": published,
            "updated_date": updated,
            "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf",
            "paper_url": f"https://arxiv.org/abs/{arxiv_id}",
        }
    except Exception as e:
        logger.warning(f"Error parsing OAI-PMH record: {e}")
        return None


def _harvest_records(set_spec: str, from_date: Optional[str], until_date: Optional[str]) -> list[dict]:
    """Synchronous OAI-PMH harvest via Sickle. Returns list of parsed record dicts."""
    sickle = Sickle(OAI_ENDPOINT)
    kwargs = {"metadataPrefix": "arXiv", "set": set_spec}
    if from_date:
        kwargs["from"] = from_date
    if until_date:
        kwargs["until"] = until_date

    records = sickle.ListRecords(**kwargs)
    parsed = []
    for record in records:
        paper = _parse_arxiv_record(record)
        if paper:
            parsed.append(paper)
    return parsed


async def load_catalog_from_oai(
    session: AsyncSession,
    set_spec: str = "cs",
    from_date: Optional[str] = None,
    until_date: Optional[str] = None,
    batch_size: int = 500,
) -> int:
    """Harvest ArXiv papers via OAI-PMH and upsert metadata to PostgreSQL."""
    logger.info(f"Starting OAI-PMH harvest: set={set_spec}, from={from_date}, until={until_date}")

    parsed_records = await asyncio.to_thread(_harvest_records, set_spec, from_date, until_date)
    logger.info(f"Harvested {len(parsed_records)} records from OAI-PMH")

    if not parsed_records:
        return 0

    total_upserted = 0
    for i in range(0, len(parsed_records), batch_size):
        batch = parsed_records[i : i + batch_size]
        stmt = pg_insert(ArxivCatalog).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=["arxiv_id"],
            set_={
                "title": stmt.excluded.title,
                "abstract": stmt.excluded.abstract,
                "authors": stmt.excluded.authors,
                "categories": stmt.excluded.categories,
                "primary_category": stmt.excluded.primary_category,
                "updated_date": stmt.excluded.updated_date,
                "pdf_url": stmt.excluded.pdf_url,
                "paper_url": stmt.excluded.paper_url,
                "updated_at": func.now(),
                "indexed_in_qdrant": False,
            },
        )
        await session.execute(stmt)
        total_upserted += len(batch)

    await session.commit()
    logger.info(f"Upserted {total_upserted} records to PostgreSQL")
    return total_upserted


async def upsert_catalog_to_qdrant(
    session: AsyncSession,
    batch_size: int = 100,
) -> int:
    """Index unsynced catalog rows into Qdrant with server-side embedding."""
    client = get_qdrant_client()
    total_indexed = 0

    while True:
        result = await session.execute(
            select(ArxivCatalog)
            .where(ArxivCatalog.indexed_in_qdrant == False)
            .limit(batch_size)
        )
        rows = result.scalars().all()
        if not rows:
            break

        points = []
        arxiv_ids = []
        for row in rows:
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, row.arxiv_id))
            points.append(
                PointStruct(
                    id=point_id,
                    payload={
                        "arxiv_id": row.arxiv_id,
                        "title": row.title,
                        "abstract": row.abstract,
                        "authors": row.authors,
                        "categories": row.categories,
                        "primary_category": row.primary_category,
                        "published_date": row.published_date,
                        "paper_url": row.paper_url,
                        "pdf_url": row.pdf_url,
                    },
                    vector={
                        CATALOG_EMBED_MODEL: Document(
                            text=f"{row.title} {row.abstract}",
                            model=CATALOG_EMBED_MODEL,
                        )
                    },
                )
            )
            arxiv_ids.append(row.arxiv_id)

        await asyncio.to_thread(
            client.upsert,
            collection_name=CATALOG_COLLECTION,
            points=points,
        )

        from sqlalchemy import update
        await session.execute(
            update(ArxivCatalog)
            .where(ArxivCatalog.arxiv_id.in_(arxiv_ids))
            .values(indexed_in_qdrant=True)
        )
        await session.commit()
        total_indexed += len(rows)
        logger.info(f"Indexed {total_indexed} catalog rows in Qdrant so far")

    logger.info(f"Qdrant catalog indexing complete: {total_indexed} rows indexed")
    return total_indexed
