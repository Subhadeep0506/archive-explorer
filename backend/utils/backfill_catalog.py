"""
Backfill ArXiv catalog: harvest CS papers via OAI-PMH → PostgreSQL → Qdrant.

Usage (from backend/):
    python -m utils.backfill_catalog                          # last 5 years, all CS
    python -m utils.backfill_catalog --years 2                # last 2 years
    python -m utils.backfill_catalog --from 2024-01-01 --until 2024-06-30
    python -m utils.backfill_catalog --set-spec cs.AI         # subcategory (auto-converted to cs:cs:AI)
    python -m utils.backfill_catalog --qdrant-only            # skip harvest, just index pending rows
    python -m utils.backfill_catalog --chunk-days 14          # smaller time slices (helps with timeouts)

Requires: DATABASE_URL, QDRANT_URI, QDRANT_API_KEY in .env (loaded automatically).
"""

import argparse
import asyncio
import math
import sys
import time
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn, MofNCompleteColumn

from src.database.db import session_pool
from src.core.catalog_engine.ingest import load_catalog_from_oai, upsert_catalog_to_qdrant
from src.lib.qdrant import ensure_collections_exist

console = Console()

# ArXiv OAI-PMH uses colon-separated set specs (e.g. cs:cs:AI), not dots.
SUBCATEGORY_MAP = {
    "cs": "cs", "math": "math", "stat": "stat", "eess": "eess",
    "econ": "econ", "q-bio": "q-bio", "q-fin": "q-fin",
}

def _normalize_set_spec(spec: str) -> str:
    """Convert dotted notation (cs.AI) to OAI-PMH format (cs:cs:AI)."""
    if ":" in spec:
        return spec
    parts = spec.split(".", 1)
    top = parts[0]
    if len(parts) == 1:
        return top
    return f"{top}:{top}:{parts[1]}"


def _retry(fn, description: str, max_retries: int = 5, base_delay: float = 3.0):
    """Call a sync function with retries on transient network errors."""
    for attempt in range(1, max_retries + 1):
        try:
            return fn()
        except Exception as e:
            err_msg = str(e).lower()
            is_transient = any(s in err_msg for s in ["getaddrinfo", "connecterror", "timed out", "connection reset"])
            if not is_transient or attempt == max_retries:
                raise
            delay = base_delay * attempt
            console.print(f"[yellow]  {description} failed (attempt {attempt}/{max_retries}): {e}[/yellow]")
            console.print(f"[yellow]  Retrying in {delay:.0f}s...[/yellow]")
            time.sleep(delay)


async def backfill(
    set_spec: str,
    start: date,
    end: date,
    chunk_days: int,
    qdrant_only: bool,
):
    console.print("[bold]Ensuring Qdrant collections exist...[/bold]")
    await asyncio.to_thread(_retry, ensure_collections_exist, "Qdrant connection")

    total_harvested = 0
    total_indexed = 0

    if not qdrant_only:
        chunk = timedelta(days=chunk_days)
        total_chunks = math.ceil((end - start).days / chunk_days)

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            harvest_task = progress.add_task("Harvesting", total=total_chunks)
            cursor = start

            while cursor < end:
                until = min(cursor + chunk, end)
                from_str = cursor.isoformat()
                until_str = until.isoformat()

                progress.update(harvest_task, description=f"Harvesting {from_str} → {until_str}")
                try:
                    async with session_pool() as session:
                        count = await load_catalog_from_oai(
                            session,
                            set_spec=set_spec,
                            from_date=from_str,
                            until_date=until_str,
                        )
                        total_harvested += count
                except Exception as e:
                    console.print(f"[red]  ERROR {from_str}→{until_str}: {e}[/red]")

                progress.advance(harvest_task)
                cursor = until

        console.print(f"[green]Harvest complete: {total_harvested} records upserted to PostgreSQL[/green]")

    console.print("\n[bold]Indexing pending rows into Qdrant...[/bold]")
    async with session_pool() as session:
        total_indexed = await upsert_catalog_to_qdrant(session, batch_size=200, show_progress=True)

    console.print(f"\n[bold green]Done. Harvested: {total_harvested} | Indexed to Qdrant: {total_indexed}[/bold green]")


def main():
    parser = argparse.ArgumentParser(description="Backfill ArXiv catalog from OAI-PMH")
    parser.add_argument("--set-spec", default="cs", help="OAI-PMH set (default: cs)")
    parser.add_argument("--years", type=int, default=5, help="How many years back (default: 5)")
    parser.add_argument("--from", dest="from_date", help="Override start date (YYYY-MM-DD)")
    parser.add_argument("--until", dest="until_date", help="Override end date (YYYY-MM-DD)")
    parser.add_argument("--chunk-days", type=int, default=30, help="Days per OAI-PMH request (default: 30)")
    parser.add_argument("--qdrant-only", action="store_true", help="Skip harvest, only index pending rows to Qdrant")
    args = parser.parse_args()

    if args.from_date:
        start = date.fromisoformat(args.from_date)
    else:
        start = date.today() - timedelta(days=365 * args.years)

    end = date.fromisoformat(args.until_date) if args.until_date else date.today()

    set_spec = _normalize_set_spec(args.set_spec)
    print(f"Backfill: {set_spec} | {start} → {end} | chunks={args.chunk_days}d")
    asyncio.run(backfill(set_spec, start, end, args.chunk_days, args.qdrant_only))


if __name__ == "__main__":
    main()
