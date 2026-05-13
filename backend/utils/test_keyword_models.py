"""
Keyword Extraction Model Comparison Script

Tests ONNX-only models:
1. KeyBERT + SciBERT INT8 ONNX (local: resources/keyword_extract_model/) - Production model

All models run fully locally — no HuggingFace weight download.
Only the SciBERT tokenizer (~1 MB config) is fetched once and cached.

Optimizations:
- ORT_ENABLE_ALL graph optimization
- Parallel intra/inter-op threading (all CPU cores)
- Batch size 32 for embedding
- Concurrent paper extraction via ThreadPoolExecutor

Metrics: Speed, quality impression, memory usage
"""

import os
import time
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Tuple
import json

try:
    from keybert import KeyBERT
except ImportError:
    import subprocess

    subprocess.run(["pip", "install", "keybert"], check=True)
    from keybert import KeyBERT

from onnx_embedder import ONNXSentenceEmbedder, _RESOURCE_DIR, _INT8_MODEL

TEST_PAPERS = [
    {
        "title": "Attention Is All You Need",
        "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. In an encoder-decoder configuration. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train.",
    },
    {
        "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "abstract": "We introduce BERT, a new method of pre-training language representations. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers. As a result, the pre-trained BERT model can be fine-tuned with just one additional output layer to create state-of-the-art models for a wide range of tasks, such as question answering and language inference, without substantial task-specific architecture modifications.",
    },
    {
        "title": "LSTM: A Search Space Odyssey",
        "abstract": "Several variants of the long short-term memory (LSTM) architecture have been proposed, each with different numbers of gates and activations. The question of what works best for LSTMs has not yet been answered. We conduct the first systematic study to compare different LSTM variants and provide practical recommendations for practitioners.",
    },
    {
        "title": "Graph Convolutional Networks for Semi-Supervised Node Classification",
        "abstract": "We present a scalable approach for semi-supervised learning on graphs based on an efficient variant of convolutional neural networks that operate directly on graphs. The method is based on a localized first-order approximation of spectral graph convolutions. Our framework combines neural networks with the non-Euclidean structure of graphs, enabling end-to-end learning of hidden layer representations for tasks on graphs.",
    },
    {
        "title": "Deep Residual Learning for Image Recognition",
        "abstract": "Very deep convolutional networks have led to groundbreaking advances in image recognition. However, as networks become increasingly deep, they become harder to train due to the vanishing gradient problem. To address this, we introduce a residual learning framework to ease training of networks that are substantially deeper than previously practical. We explicitly reformulate the layers as learning residual functions with reference to the layer inputs, instead of learning unreferenced functions.",
    },
]


class KeywordModel:
    """Base class for keyword extraction models"""

    def __init__(self, name: str):
        self.name = name
        self.model = None
        self.load_time = 0.0

    def load(self):
        """Load the model - override in subclasses"""
        raise NotImplementedError

    def extract(self, title: str, abstract: str, top_n: int = 10) -> List[str]:
        """Extract keywords - override in subclasses"""
        raise NotImplementedError


class ONNXSciBERTModel(KeywordModel):
    """
    KeyBERT backed by a local SciBERT ONNX model.

    Loads the ONNX session directly from disk — no HuggingFace model download.
    Only the tokenizer config/vocab (~1 MB) is fetched on first run and cached
    in ~/.cache/huggingface/.
    """

    def __init__(self, name: str, onnx_path: Path):
        super().__init__(name)
        self.onnx_path = onnx_path

    def load(self):
        if not self.onnx_path.exists():
            raise FileNotFoundError(f"ONNX model not found: {self.onnx_path}")
        start = time.time()
        embedder = ONNXSentenceEmbedder(self.onnx_path)
        self.model = KeyBERT(model=embedder)
        self.load_time = time.time() - start

    def extract(self, title: str, abstract: str, top_n: int = 10) -> List[dict]:
        text = f"{title}. {abstract}"
        results = self.model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 3),
            stop_words="english",
            use_mmr=True,
            diversity=0.6,
            top_n=top_n,
        )
        return sorted([{"keyword": kw, "score": score} for kw, score in results], key=lambda x: x["score"], reverse=True)


class KeywordBenchmark:
    def __init__(self, db_path: str = "keyword_test_results.db"):
        self.db_path = db_path
        self.results = []
        self._init_db()

    def _init_db(self):
        """Create SQLite table for results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS benchmark_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT,
                paper_title TEXT,
                load_time_ms FLOAT,
                extraction_time_ms FLOAT,
                keywords TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def save_result(
        self,
        model_name: str,
        paper_title: str,
        load_time_ms: float,
        extraction_time_ms: float,
        keywords: List[dict],
    ):
        """Save benchmark result to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO benchmark_results
            (model_name, paper_title, load_time_ms, extraction_time_ms, keywords)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                model_name,
                paper_title,
                load_time_ms,
                extraction_time_ms,
                json.dumps(keywords),
            ),
        )
        conn.commit()
        conn.close()

    def run(self, models: List[KeywordModel], papers: List[dict] = None):
        """Run benchmark on all models"""
        if papers is None:
            papers = TEST_PAPERS

        print("\n" + "=" * 100)
        print("KEYWORD EXTRACTION MODEL COMPARISON")
        print("=" * 100)

        # Load all models
        print("\n[LOADING MODELS]")
        for model in models:
            print(f"  Loading {model.name}...", end=" ", flush=True)
            try:
                model.load()
                print(f"OK ({model.load_time:.2f}s)")
            except Exception as e:
                print(f"ERROR: {str(e)}")
                continue

        # Run extraction benchmark
        print("\n[EXTRACTION BENCHMARK]")
        print(f"Testing {len(models)} models on {len(papers)} papers...\n")

        for model in models:
            if model.model is None:  # Skip failed loads
                continue

            print(f"\n{'-' * 100}")
            print(f"Model: {model.name}")
            print(f"Load Time: {model.load_time * 1000:.2f} ms")
            print(f"{'-' * 100}")

            extraction_times = [None] * len(papers)
            print_lock = threading.Lock()

            def _extract_one(idx_paper):
                idx, paper = idx_paper
                try:
                    start = time.time()
                    keywords = model.extract(
                        paper["title"], paper["abstract"], top_n=10
                    )
                    elapsed = (time.time() - start) * 1000
                    self.save_result(
                        model.name,
                        paper["title"],
                        model.load_time * 1000,
                        elapsed,
                        keywords,
                    )
                    with print_lock:
                        print(f"  Paper: {paper['title'][:60]}...  OK {elapsed:.1f}ms")
                        kw_preview = [kw["keyword"] for kw in keywords[:5]]
                        suffix = "..." if len(keywords) > 5 else ""
                        print(f"    Keywords: {', '.join(kw_preview)}{suffix}")
                    return idx, elapsed
                except Exception as e:
                    with print_lock:
                        print(f"  Paper: {paper['title'][:60]}...  ERROR: {e}")
                    return idx, None

            max_workers = min(len(papers), os.cpu_count() or 4)
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = [
                    pool.submit(_extract_one, (i, p)) for i, p in enumerate(papers)
                ]
                for fut in as_completed(futures):
                    idx, elapsed = fut.result()
                    extraction_times[idx] = elapsed

            # Summary stats
            valid_times = [t for t in extraction_times if t is not None]
            if valid_times:
                print(
                    f"\n  Avg Extraction Time: {sum(valid_times) / len(valid_times):.1f} ms"
                )
                print(
                    f"  Min: {min(valid_times):.1f} ms, Max: {max(valid_times):.1f} ms"
                )

        print("\n" + "=" * 100)
        print(f"Results saved to: {self.db_path}")
        print("=" * 100)

    def print_summary(self):
        """Print summary statistics from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        print("\n[SUMMARY STATISTICS]")
        print("Average metrics by model:\n")

        cursor.execute("""
            SELECT model_name,
                   COUNT(*) as num_runs,
                   AVG(load_time_ms) as avg_load_ms,
                   AVG(extraction_time_ms) as avg_extraction_ms,
                   MIN(extraction_time_ms) as min_extraction_ms,
                   MAX(extraction_time_ms) as max_extraction_ms
            FROM benchmark_results
            GROUP BY model_name
            ORDER BY avg_extraction_ms ASC
        """)

        for row in cursor.fetchall():
            model, runs, load_ms, ext_ms, min_ext, max_ext = row
            print(f"{model}")
            print(f"  Runs: {runs}")
            print(f"  Load Time: {load_ms:.2f} ms")
            print(
                f"  Extraction: {ext_ms:.2f} ms (min: {min_ext:.2f}, max: {max_ext:.2f})"
            )
            print()

        conn.close()


def main():
    print("\nInitializing keyword extraction models...")
    print(f"ONNX model directory: {_RESOURCE_DIR}\n")

    # Validate model files exist
    for path, label in [(_INT8_MODEL, "INT8")]:
        status = "found" if path.exists() else "NOT FOUND"
        print(f"  {label:8} model ({path.name}): {status}")
    print()

    models: List[KeywordModel] = [
        ONNXSciBERTModel(
            "SciBERT INT8 ONNX (local)",
            _INT8_MODEL,
        ),
    ]

    # Run benchmark
    benchmark = KeywordBenchmark()
    benchmark.run(models, TEST_PAPERS)
    benchmark.print_summary()

    print("\nOK Benchmark complete!")
    print(f"Detailed results saved to: keyword_test_results.db")
    print("\nTo view results, run:")
    print("  sqlite3 keyword_test_results.db")
    print(
        "  SELECT model_name, paper_title, extraction_time_ms, keywords"
        " FROM benchmark_results ORDER BY model_name;"
    )


if __name__ == "__main__":
    main()
