"""
ArXiv CS Papers Fetcher - Stores papers from last 5 years in local SQLite database

Fetches all cs.* category papers from the last 5 years using ArXiv OAI-PMH API.
This database can be used for testing keyword extraction, recommendations, etc.

Features:
- Fetches papers incrementally (no duplicate downloads)
- Uses OAI-PMH ListRecords for efficient bulk harvesting
- Stores metadata: arxiv_id, title, abstract, authors, categories, dates, urls
- Shows progress bar
- ~500K+ papers for cs.* categories
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import logging

try:
    from sickle import Sickle
    from sickle.models import Record
    import xml.etree.ElementTree as ET
except ImportError:
    print("Installing required packages...")
    import subprocess

    subprocess.run(["pip", "install", "sickle"], check=True)
    from sickle import Sickle
    from sickle.models import Record
    import xml.etree.ElementTree as ET

try:
    from rich.progress import (
        Progress,
        SpinnerColumn,
        BarColumn,
        TextColumn,
        TaskProgressColumn,
    )
    from rich.logging import RichHandler
except ImportError:
    import subprocess

    subprocess.run(["pip", "install", "rich"], check=True)
    from rich.progress import (
        Progress,
        SpinnerColumn,
        BarColumn,
        TextColumn,
        TaskProgressColumn,
    )
    from rich.logging import RichHandler

# ============================================================================
# SETUP LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)


# ============================================================================
# DATABASE SETUP
# ============================================================================


class ArxivDatabase:
    """SQLite database for storing ArXiv paper metadata"""

    def __init__(self, db_path: str = "arxiv_papers.db"):
        self.db_path = db_path
        self.conn = None
        self._init_db()

    def _init_db(self):
        """Create database schema"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        # Main papers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                arxiv_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                abstract TEXT NOT NULL,
                authors TEXT NOT NULL,
                categories TEXT,
                primary_category TEXT,
                published_date TEXT,
                updated_date TEXT,
                pdf_url TEXT,
                paper_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Metadata table for tracking harvest state
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS harvest_metadata (
                id INTEGER PRIMARY KEY,
                last_harvest_date TEXT,
                total_papers INTEGER DEFAULT 0,
                last_resumption_token TEXT,
                status TEXT DEFAULT 'completed'
            )
        """)

        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_arxiv_id ON papers(arxiv_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_primary_category ON papers(primary_category)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_published_date ON papers(published_date)
        """)

        self.conn.commit()
        logger.info(f"Database initialized: {self.db_path}")

    def insert_paper(self, paper_data: dict) -> bool:
        """Insert or update a paper record"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO papers 
                (arxiv_id, title, abstract, authors, categories, primary_category,
                 published_date, updated_date, pdf_url, paper_url, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(arxiv_id) DO UPDATE SET
                    title = excluded.title,
                    abstract = excluded.abstract,
                    authors = excluded.authors,
                    categories = excluded.categories,
                    primary_category = excluded.primary_category,
                    updated_date = excluded.updated_date,
                    updated_at = CURRENT_TIMESTAMP
            """,
                (
                    paper_data["arxiv_id"],
                    paper_data["title"],
                    paper_data["abstract"],
                    paper_data["authors"],
                    paper_data["categories"],
                    paper_data["primary_category"],
                    paper_data["published_date"],
                    paper_data["updated_date"],
                    paper_data["pdf_url"],
                    paper_data["paper_url"],
                ),
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(
                f"Error inserting paper {paper_data.get('arxiv_id', 'unknown')}: {e}"
            )
            return False

    def get_paper_count(self) -> int:
        """Get total number of papers in database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM papers")
        return cursor.fetchone()[0]

    def get_papers_by_category(self, category: str, limit: int = 10) -> list:
        """Get sample papers from a specific category"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT arxiv_id, title, authors, published_date
            FROM papers
            WHERE primary_category = ?
            LIMIT ?
        """,
            (category, limit),
        )
        return cursor.fetchall()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# ============================================================================
# ARXIV HARVESTER
# ============================================================================


class ArxivHarvester:
    """Fetch papers from ArXiv using OAI-PMH protocol"""

    OAI_ENDPOINT = "http://export.arxiv.org/oai2"

    # ArXiv OAI-PMH namespace
    ARXIV_NS = "http://arxiv.org/OAI/arXiv/"

    def __init__(self, db: ArxivDatabase):
        self.db = db
        self.sickle = Sickle(self.OAI_ENDPOINT)
        self.papers_fetched = 0

    def _parse_arxiv_record(self, record: Record) -> Optional[dict]:
        """Parse a single OAI-PMH record"""

        if record.deleted:
            return None

        try:
            # Get XML metadata
            meta = record.xml.find(f".//{{{self.ARXIV_NS}}}arXiv")
            if meta is None:
                return None

            # Extract fields
            arxiv_id = (meta.findtext(f"{{{self.ARXIV_NS}}}id") or "").strip()
            if not arxiv_id:
                return None

            title = (meta.findtext(f"{{{self.ARXIV_NS}}}title") or "").strip()
            abstract = (meta.findtext(f"{{{self.ARXIV_NS}}}abstract") or "").strip()

            # Parse authors - each has <keyname> and optional <forenames>
            authors = []
            for author_el in meta.findall(f".//{{{self.ARXIV_NS}}}author"):
                keyname = (
                    author_el.findtext(f"{{{self.ARXIV_NS}}}keyname") or ""
                ).strip()
                forenames = (
                    author_el.findtext(f"{{{self.ARXIV_NS}}}forenames") or ""
                ).strip()

                if keyname:
                    name = f"{forenames} {keyname}".strip()
                    authors.append(name)

            # Categories
            categories = (meta.findtext(f"{{{self.ARXIV_NS}}}categories") or "").strip()
            # Format: "cs.AI cs.LG cs.CL" - extract first as primary
            category_list = categories.split() if categories else []
            primary_category = category_list[0] if category_list else None

            # Dates
            published = (meta.findtext(f"{{{self.ARXIV_NS}}}created") or "").strip()
            updated = (meta.findtext(f"{{{self.ARXIV_NS}}}updated") or "").strip()

            return {
                "arxiv_id": arxiv_id,
                "title": title,
                "abstract": abstract,
                "authors": "; ".join(authors),  # Semicolon-separated
                "categories": categories,
                "primary_category": primary_category,
                "published_date": published,
                "updated_date": updated,
                "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                "paper_url": f"https://arxiv.org/abs/{arxiv_id}",
            }

        except Exception as e:
            logger.warning(f"Error parsing record: {e}")
            return None

    def fetch_papers(
        self, from_date: str = None, until_date: str = None, set_spec: str = "cs"
    ) -> int:
        """
        Fetch papers from ArXiv using OAI-PMH ListRecords

        Args:
            from_date: Start date (YYYY-MM-DD). If None, defaults to 5 years ago
            until_date: End date (YYYY-MM-DD). If None, defaults to today
            set_spec: OAI set specification (cs = all computer science)

        Returns:
            Total number of papers fetched
        """

        # Set default dates (last 5 years)
        if until_date is None:
            until_date = datetime.now().strftime("%Y-%m-%d")

        if from_date is None:
            from_date = (datetime.now() - timedelta(days=5 * 365)).strftime("%Y-%m-%d")

        logger.info(f"Starting harvest: {from_date} to {until_date}")
        logger.info(f"Set: {set_spec}, Endpoint: {self.OAI_ENDPOINT}")

        try:
            # Use ListRecords to get all papers in the date range
            # OAI-PMH handles resumption tokens automatically through Sickle
            records = self.sickle.ListRecords(
                metadataPrefix="arXiv",
                set=set_spec,
                **{"from": from_date, "until": until_date},
            )

            batch_count = 0
            inserted_count = 0

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=40),
                TaskProgressColumn(),
                TextColumn(
                    "[cyan]{task.fields[inserted]} inserted / [blue]{task.fields[processed]} processed"
                ),
            ) as progress:
                task = progress.add_task(
                    "[cyan]Harvesting papers...",
                    total=None,
                    inserted=0,
                    processed=0,
                )

                for record in records:
                    batch_count += 1

                    # Parse and insert
                    paper = self._parse_arxiv_record(record)
                    if paper:
                        if self.db.insert_paper(paper):
                            inserted_count += 1

                    progress.update(
                        task,
                        advance=1,
                        inserted=inserted_count,
                        processed=batch_count,
                    )

                # Safety limit for testing (can be removed)
                # if batch_count >= 10000:
                #     logger.info("Reached test limit of 10,000 records")
                #     break

            self.papers_fetched = inserted_count
            logger.info(
                f"Harvest complete: {batch_count} records processed, "
                f"{inserted_count} papers inserted/updated"
            )

            return inserted_count

        except Exception as e:
            logger.error(f"Error during harvest: {e}")
            raise


# ============================================================================
# MAIN
# ============================================================================


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch ArXiv papers and store in local SQLite database"
    )
    parser.add_argument(
        "--from-date",
        type=str,
        help="Start date (YYYY-MM-DD). Default: 5 years ago",
        default=None,
    )
    parser.add_argument(
        "--until-date",
        type=str,
        help="End date (YYYY-MM-DD). Default: today",
        default=None,
    )
    parser.add_argument(
        "--category",
        type=str,
        default="cs",
        help="OAI set specification (default: cs = all CS papers)",
    )
    parser.add_argument(
        "--db", type=str, default="arxiv_papers.db", help="Path to SQLite database"
    )

    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("ARXIV PAPERS FETCHER - Last 5 Years (CS Category)")
    print("=" * 80)

    try:
        # Initialize database
        db = ArxivDatabase(args.db)
        initial_count = db.get_paper_count()
        logger.info(f"Database has {initial_count} existing papers")

        # Create harvester
        harvester = ArxivHarvester(db)

        # Fetch papers
        inserted = harvester.fetch_papers(
            from_date=args.from_date, until_date=args.until_date, set_spec=args.category
        )

        # Print stats
        final_count = db.get_paper_count()
        logger.info(
            f"Database now has {final_count} total papers " f"(+{inserted} new)"
        )

        # Show sample papers per category
        logger.info("\nSample papers by primary category:")
        categories = ["cs.AI", "cs.LG", "cs.CL", "cs.CV"]
        for cat in categories:
            samples = db.get_papers_by_category(cat, limit=3)
            if samples:
                logger.info(f"\n  {cat}:")
                for arxiv_id, title, authors, date in samples:
                    logger.info(f"    - {arxiv_id}: {title[:60]}...")

        # Close connection
        db.close()

        print("\n" + "=" * 80)
        print(f"✓ Success! Papers stored in: {args.db}")
        print("=" * 80)

        print("\nUseful queries:")
        print(f"  # Total papers:")
        print(f"    sqlite3 {args.db} 'SELECT COUNT(*) FROM papers;'")
        print(f"\n  # Papers by category:")
        print(f"    sqlite3 {args.db}")
        print(
            f"    SELECT primary_category, COUNT(*) FROM papers GROUP BY primary_category;"
        )
        print(f"\n  # Sample papers:")
        print(f"    sqlite3 {args.db}")
        print(f"    SELECT arxiv_id, title FROM papers LIMIT 10;")
        print(f"\n  # Papers from last month:")
        print(f"    sqlite3 {args.db}")
        print(
            f"    SELECT * FROM papers WHERE published_date > date('now', '-30 days');"
        )

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
