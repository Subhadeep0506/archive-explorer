"""
Test Keyword Extraction on Real ArXiv Papers from SQLite Database

This script:
1. Connects to the arxiv_papers.db created by fetch_arxiv_papers.py
2. Samples papers from different categories
3. Tests keyword extraction models on real data using LOCAL ONNX models
4. Compares quality, speed, and diversity of keywords
5. Generates a comparison report

ONNX models used (no HuggingFace weight download):
  - scibert_scivocab_uncased-int8.onnx   (INT8 quantized)
  - scibert_scivocab_uncased_model_q4f16.onnx (Q4F16 quantized)
Both files must exist in: backend/resources/keyword_extract_model/
"""

import sqlite3
import time
from pathlib import Path
from typing import List, Dict, Tuple

try:
    from keybert import KeyBERT
except ImportError:
    import subprocess

    subprocess.run(["pip", "install", "keybert"], check=True)
    from keybert import KeyBERT

try:
    from rich.progress import (
        Progress,
        SpinnerColumn,
        BarColumn,
        TextColumn,
        TaskProgressColumn,
    )
    from rich.console import Console
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
    from rich.console import Console

console = Console()

from onnx_embedder import ONNXSentenceEmbedder, _RESOURCE_DIR, _INT8_MODEL, _Q4F16_MODEL


class ArxivPaperLoader:
    """Load papers from arxiv_papers.db"""

    def __init__(self, db_path: str = "arxiv_papers.db"):
        self.db_path = db_path

    def get_papers_by_category(self, category: str, limit: int = 5) -> List[Dict]:
        """Get sample papers from a specific category"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT arxiv_id, title, abstract, authors, primary_category, published_date
            FROM papers
            WHERE primary_category = ?
            ORDER BY RANDOM()
            LIMIT ?
        """,
            (category, limit),
        )

        papers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return papers

    def get_random_papers(self, limit: int = 20) -> List[Dict]:
        """Get random papers from all categories"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT arxiv_id, title, abstract, authors, primary_category, published_date
            FROM papers
            ORDER BY RANDOM()
            LIMIT ?
        """,
            (limit,),
        )

        papers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return papers

    def get_categories(self) -> List[Tuple]:
        """Get all categories and their paper counts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT primary_category, COUNT(*) as count
            FROM papers
            GROUP BY primary_category
            ORDER BY count DESC
        """)

        categories = cursor.fetchall()
        conn.close()
        return categories


class KeywordExtractorBatch:
    """Batch keyword extraction tester using local ONNX models"""

    def __init__(self):
        self.models: Dict[str, KeyBERT] = {}
        self.load_time: Dict[str, float] = {}

    def add_onnx_model(self, name: str, onnx_path: Path):
        """Load a local ONNX model and register it for extraction."""
        if not onnx_path.exists():
            console.print(f"[red]✗[/red] {name}: model file not found at {onnx_path}")
            return

        with Progress(SpinnerColumn(), TextColumn(f"[cyan]Loading {name}...")) as p:
            p.add_task("", total=None)
            start = time.time()
            try:
                embedder = ONNXSentenceEmbedder(onnx_path)
                self.models[name] = KeyBERT(model=embedder)
                self.load_time[name] = time.time() - start
            except Exception as e:
                console.print(f"[red]✗[/red] {name} failed to load: {e}")
                return

        console.print(f"[green]✓[/green] {name} loaded in {self.load_time[name]:.2f}s")

    def extract(
        self, name: str, title: str, abstract: str, top_n: int = 10
    ) -> List[str]:
        """Extract keywords using a specific model"""
        if name not in self.models:
            raise ValueError(f"Model {name} not loaded")

        text = f"{title}. {abstract[:1200]}"
        keywords = self.models[name].extract_keywords(
            text,
            keyphrase_ngram_range=(1, 3),
            stop_words="english",
            use_mmr=True,
            diversity=0.6,
            top_n=top_n,
        )
        return [kw for kw, _ in keywords]


class KeywordComparisonAnalyzer:
    """Analyze and compare keyword extraction results"""

    def __init__(self, output_file: str = "keyword_comparison_report.txt"):
        self.output_file = output_file
        self.results = []

    def compare_keywords_on_paper(self, paper: Dict, extractors: Dict[str, List[str]]):
        """Compare keyword extraction results for a single paper"""

        result = {
            "arxiv_id": paper["arxiv_id"],
            "title": paper["title"][:70],
            "category": paper["primary_category"],
            "extractors": extractors,
        }

        # Calculate overlap between models
        all_keywords = set()
        for keywords in extractors.values():
            all_keywords.update(keywords)

        overlap = {}
        for name1, keywords1 in extractors.items():
            for name2, keywords2 in extractors.items():
                if name1 < name2:
                    shared = set(keywords1) & set(keywords2)
                    overlap[f"{name1} ∩ {name2}"] = len(shared)

        result["overlap"] = overlap
        self.results.append(result)

    def generate_report(self):
        """Generate comparison report"""

        with open(self.output_file, "w") as f:
            f.write("=" * 100 + "\n")
            f.write("KEYWORD EXTRACTION MODEL COMPARISON ON REAL ARXIV PAPERS\n")
            f.write("=" * 100 + "\n\n")

            # Summary stats
            f.write(f"Total papers analyzed: {len(self.results)}\n\n")

            # Detailed results
            for i, result in enumerate(self.results, 1):
                f.write(f"\n{i}. {result['arxiv_id']} ({result['category']})\n")
                f.write(f"   Title: {result['title']}\n")
                f.write("   " + "-" * 96 + "\n")

                for model_name, keywords in result["extractors"].items():
                    f.write(f"   {model_name}:\n")
                    f.write(f"     {', '.join(keywords[:8])}")
                    if len(keywords) > 8:
                        f.write(f", ...")
                    f.write("\n")

                if result["overlap"]:
                    f.write("   Overlap:\n")
                    for overlap_pair, count in result["overlap"].items():
                        f.write(f"     {overlap_pair}: {count}/10\n")

        console.print(f"\n[green]Report saved to:[/green] {self.output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Test keyword extraction models on real ArXiv papers"
    )
    parser.add_argument(
        "--db", type=str, default="arxiv_papers.db", help="Path to arxiv_papers.db"
    )
    parser.add_argument(
        "--category",
        type=str,
        help="Test specific category (e.g., cs.AI). If not set, test random papers",
        default=None,
    )
    parser.add_argument(
        "--num-papers",
        type=int,
        default=5,
        help="Number of papers to test per category",
    )
    parser.add_argument(
        "--show-categories",
        action="store_true",
        help="Show available categories and exit",
    )

    args = parser.parse_args()

    # Load papers
    print("\nLoading papers from database...")
    loader = ArxivPaperLoader(args.db)

    # Show categories if requested
    if args.show_categories:
        categories = loader.get_categories()
        print(f"\nAvailable categories ({len(categories)} total):\n")
        for cat, count in categories:
            print(f"  {cat:15} {count:6} papers")
        return

    # Load papers
    if args.category:
        papers = loader.get_papers_by_category(args.category, limit=args.num_papers)
        print(f"Loaded {len(papers)} papers from {args.category}")
    else:
        papers = loader.get_random_papers(limit=args.num_papers)
        print(f"Loaded {len(papers)} random papers")

    if not papers:
        print("No papers found in database!")
        return

    # Initialize models
    console.print("\n[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("[bold]INITIALIZING ONNX MODELS[/bold]")
    console.print(f"[dim]Model directory: {_RESOURCE_DIR}[/dim]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]\n")

    extractor = KeywordExtractorBatch()

    # Load local ONNX SciBERT variants (no HuggingFace weight download)
    extractor.add_onnx_model("SciBERT INT8 ONNX", _INT8_MODEL)
    extractor.add_onnx_model("SciBERT Q4F16 ONNX", _Q4F16_MODEL)

    if not extractor.models:
        console.print("[red]No models loaded — cannot continue.[/red]")
        return

    # Extract keywords
    console.print("\n[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("[bold]EXTRACTING KEYWORDS FROM PAPERS[/bold]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]\n")

    analyzer = KeywordComparisonAnalyzer()

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
    ) as progress:
        paper_task = progress.add_task(
            f"[cyan]Testing {len(papers)} papers...", total=len(papers)
        )

        for i, paper in enumerate(papers, 1):
            console.print(
                f"[bold cyan]Paper {i}/{len(papers)}:[/bold cyan] {paper['arxiv_id']} ({paper['primary_category']})"
            )
            console.print(f"  [yellow]{paper['title'][:70]}...[/yellow]")

            extractors = {}

            for model_name in extractor.models.keys():
                try:
                    start = time.time()
                    keywords = extractor.extract(
                        model_name, paper["title"], paper["abstract"], top_n=10
                    )
                    elapsed = (time.time() - start) * 1000

                    extractors[model_name] = keywords

                    keywords_display = ", ".join(keywords[:8])
                    if len(keywords) > 8:
                        keywords_display += ", ..."
                    console.print(f"  [green]✓[/green] {model_name}: {elapsed:.0f}ms")
                    console.print(f"    [dim]{keywords_display}[/dim]")

                except Exception as e:
                    console.print(f"  [red]✗[/red] {model_name}: {e}")

            analyzer.compare_keywords_on_paper(paper, extractors)
            progress.update(paper_task, advance=1)
            console.print()

    # Generate report
    console.print("\n[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("[bold]Generating Report...[/bold]")
    analyzer.generate_report()
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")

    # Print quick summary
    console.print("\n[bold]QUICK SUMMARY — Model load times:[/bold]")
    for model_name, load_time in extractor.load_time.items():
        console.print(
            f"  [cyan]{model_name:40}[/cyan] [green]{load_time * 1000:.0f} ms[/green]"
        )

    console.print(f"\n[bold]To view detailed report:[/bold]")
    console.print(f"  [dim]cat keyword_comparison_report.txt[/dim]")


if __name__ == "__main__":
    main()
