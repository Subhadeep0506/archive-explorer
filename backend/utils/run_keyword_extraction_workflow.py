#!/usr/bin/env python
"""
ORCHESTRATION SCRIPT - Run keyword extraction workflow in correct order:
1. Fetch ArXiv papers (30-60 min)
2. Test keyword extraction models on real data (10-15 min)

Usage:
    python run_keyword_extraction_workflow.py
    python run_keyword_extraction_workflow.py --skip-fetch  # Only test on existing data
    python run_keyword_extraction_workflow.py --fetch-only  # Only download papers
"""

import subprocess
import sys
import argparse
from pathlib import Path
import time

try:
    from rich.console import Console
    from rich.panel import Panel
except ImportError:
    subprocess.run(["pip", "install", "rich"], check=True)
    from rich.console import Console
    from rich.panel import Panel

console = Console()


def run_command(cmd, description):
    """Run a command and report status"""
    console.print("\n[bold cyan]" + "=" * 100 + "[/bold cyan]")
    console.print(f"[bold cyan]STEP: {description}[/bold cyan]")
    console.print("[bold cyan]" + "=" * 100 + "[/bold cyan]\n")

    try:
        result = subprocess.run(cmd, shell=True)
        if result.returncode == 0:
            console.print(f"\n[green]✓ {description} completed successfully[/green]")
            return True
        else:
            console.print(
                f"\n[red]✗ {description} failed with exit code {result.returncode}[/red]"
            )
            return False
    except Exception as e:
        console.print(f"\n[red]✗ {description} failed with error: {e}[/red]")
        return False


def check_database(db_path):
    """Check if database has papers"""
    try:
        import sqlite3

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM papers")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Keyword extraction workflow orchestration"
    )
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        help="Skip data fetching, only test on existing data",
    )
    parser.add_argument(
        "--fetch-only", action="store_true", help="Only fetch data, don't test"
    )
    parser.add_argument(
        "--test-only",
        action="store_true",
        help="Only test, don't fetch (requires existing database)",
    )
    parser.add_argument(
        "--num-papers",
        type=int,
        default=10,
        help="Number of papers to test (default: 10)",
    )

    args = parser.parse_args()

    console.print("\n[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("[bold]KEYWORD EXTRACTION WORKFLOW[/bold]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("\n[bold]Correct order:[/bold]")
    console.print("[cyan]  1. Download ArXiv papers (real data)[/cyan]")
    console.print("[cyan]  2. Test keyword extraction models on real papers[/cyan]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")

    # Check if database exists
    db_path = "arxiv_papers.db"
    existing_papers = check_database(db_path)

    if existing_papers > 0:
        console.print(
            f"\n[green]✓ Found existing database with {existing_papers} papers[/green]"
        )
    else:
        console.print(f"\n[yellow]⚠ No existing database found[/yellow]")

    # Step 1: Fetch papers
    if not args.test_only and not args.skip_fetch:
        console.print(f"\n[bold]⏱ Starting data download...[/bold]")
        console.print(f"[cyan]  This will take 30-60 minutes on first run[/cyan]")
        console.print(f"[cyan]  (Can run overnight or in background)[/cyan]")

        response = input("\nContinue with data download? (y/n) ")
        if response.lower() == "y":
            start_time = time.time()
            success = run_command(
                "python fetch_arxiv_papers.py", "Download ArXiv papers (last 5 years)"
            )
            elapsed = time.time() - start_time
            console.print(f"\n[cyan]Time elapsed: {elapsed / 60:.1f} minutes[/cyan]")

            if not success:
                console.print("\n[red]✗ Failed to download papers. Exiting.[/red]")
                sys.exit(1)

            papers_downloaded = check_database(db_path)
            console.print(
                f"\n[green]✓ Successfully downloaded/updated {papers_downloaded} papers[/green]"
            )
        else:
            console.print("\n[yellow]Skipping data download.[/yellow]")
            if existing_papers == 0:
                console.print(
                    "[red]✗ No data available to test on. Please download first.[/red]"
                )
                sys.exit(1)

    # Step 2: Test on real data
    if not args.fetch_only:
        papers_count = check_database(db_path)

        if papers_count == 0:
            console.print(
                "\n[red]✗ No papers in database. Please fetch data first:[/red]"
            )
            console.print("[cyan]   python fetch_arxiv_papers.py[/cyan]")
            sys.exit(1)

        console.print(f"\n[green]✓ Database ready with {papers_count} papers[/green]")
        console.print(f"\n[bold]⏱ Starting keyword extraction tests...[/bold]")
        console.print(
            f"[cyan]  Testing {args.num_papers} papers from your database[/cyan]"
        )
        console.print(f"[cyan]  This will take 10-15 minutes[/cyan]")

        start_time = time.time()
        success = run_command(
            f"python test_on_arxiv_data.py --num-papers {args.num_papers}",
            "Test keyword extraction models on real papers",
        )
        elapsed = time.time() - start_time
        console.print(f"\n[cyan]Time elapsed: {elapsed / 60:.1f} minutes[/cyan]")

        if success:
            console.print("\n[bold cyan]" + "=" * 80 + "[/bold cyan]")
            console.print("[bold]RESULTS[/bold]")
            console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
            console.print("\n[bold]View detailed comparison report:[/bold]")
            console.print("[cyan]  cat keyword_comparison_report.txt[/cyan]")
            console.print("\n[bold]Or check the database:[/bold]")
            console.print(
                f"[cyan]  sqlite3 {db_path} 'SELECT * FROM papers LIMIT 5;'[/cyan]"
            )
        else:
            console.print("\n[red]✗ Tests failed.[/red]")
            sys.exit(1)

    console.print("\n[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("[bold green]✓ WORKFLOW COMPLETE[/bold green]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("[cyan]1. Review keyword_comparison_report.txt[/cyan]")
    console.print("[cyan]2. Compare model performance (speed vs quality)[/cyan]")
    console.print("[cyan]3. Choose best model for production[/cyan]")
    console.print("[cyan]4. Integrate into Feature 9 (Keyword Extraction)[/cyan]")


if __name__ == "__main__":
    main()
