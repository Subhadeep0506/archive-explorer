from datetime import datetime, timedelta

from ...database.db import session_pool
from ...core.logger import SingletonLogger
from .ingest import load_catalog_from_oai, upsert_catalog_to_qdrant

logger = SingletonLogger().get_logger()


async def run_daily_catalog_update() -> dict:
    """Called by APScheduler at 02:00 UTC. Fetches yesterday's new papers and indexes them."""
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    logger.info(f"Starting daily catalog update from {yesterday}")

    try:
        async with session_pool() as session:
            new_records = await load_catalog_from_oai(session, from_date=yesterday)
            indexed = await upsert_catalog_to_qdrant(session)

        result = {"new_records": new_records, "indexed_in_qdrant": indexed}
        logger.info(f"Daily catalog update complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Daily catalog update failed: {e}")
        raise
