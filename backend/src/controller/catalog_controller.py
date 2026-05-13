from sqlalchemy import select

from ..database.db import session_pool
from ..model.arxiv_catalog import ArxivCatalog
from ..schema.arxiv import ArxivEntry
from ..core.logger import SingletonLogger

logger = SingletonLogger().get_logger()


async def get_feed(
    topics: list[str],
    start: int = 0,
    limit: int = 20,
) -> list[ArxivEntry]:
    """Query the ArXiv catalog for papers matching topics, ordered by published_date DESC."""
    async with session_pool() as session:
        stmt = (
            select(ArxivCatalog)
            .where(ArxivCatalog.primary_category.in_(topics))
            .order_by(ArxivCatalog.published_date.desc())
            .offset(start)
            .limit(limit)
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()

        return [
            ArxivEntry(
                id=str(row.id),
                arxiv_id=row.arxiv_id,
                title=row.title,
                abstract=row.abstract,
                authors=row.authors.split("; ") if row.authors else [],
                categories=row.categories.split() if row.categories else [],
                primary_category=row.primary_category,
                published=row.published_date,
                updated=row.updated_date,
                pdf_url=row.pdf_url,
                paper_url=row.paper_url,
            )
            for row in rows
        ]
