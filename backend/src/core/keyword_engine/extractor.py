"""
Keyword extraction using KeyBERT + SciBERT ONNX INT8 model.

Primary: SciBERT ONNX INT8 (~110 MB, ~80ms-2s per paper on CPU)
Fallback: FastEmbed via KeyBERT's default lightweight model

The ONNX model is auto-downloaded on first use from the URL in
KEYWORD_EXTRACTION_MODEL_URL env var, then cached locally.
Only the SciBERT tokenizer config/vocab (~1 MB) is fetched once and cached.
"""

import os
from pathlib import Path
from typing import Optional

import numpy as np
import requests
from keybert import KeyBERT

from ...core.logger import SingletonLogger

logger = SingletonLogger().get_logger()

ONNX_MODEL_DIR = Path(__file__).resolve().parents[3] / "resources" / "keyword_extract_model"
ONNX_INT8_PATH = ONNX_MODEL_DIR / "model.onnx"

_kw_model: Optional[KeyBERT] = None


def _ensure_onnx_model() -> bool:
    """Download the ONNX model from KEYWORD_EXTRACTION_MODEL_URL if not already on disk."""
    if ONNX_INT8_PATH.exists():
        return True

    url = os.environ.get("KEYWORD_EXTRACTION_MODEL_URL")
    if not url:
        logger.warning("KEYWORD_EXTRACTION_MODEL_URL not set — cannot download ONNX model")
        return False

    try:
        logger.info(f"Downloading SciBERT ONNX INT8 model from {url}")
        ONNX_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        tmp_path = ONNX_INT8_PATH.with_suffix(".onnx.tmp")

        with requests.get(url, stream=True, timeout=300) as resp:
            resp.raise_for_status()
            with open(tmp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1 << 20):
                    f.write(chunk)

        tmp_path.rename(ONNX_INT8_PATH)
        logger.info(f"ONNX model saved to {ONNX_INT8_PATH}")
        return True
    except Exception as e:
        logger.warning(f"Failed to download ONNX model: {e}")
        if tmp_path.exists():
            tmp_path.unlink()
        return False


def get_keyword_model() -> KeyBERT:
    """Lazy singleton. Downloads + loads SciBERT ONNX if available, else falls back."""
    global _kw_model
    if _kw_model is not None:
        return _kw_model

    if _ensure_onnx_model():
        try:
            logger.info(f"Loading SciBERT ONNX INT8 model from {ONNX_INT8_PATH}")
            from .onnx_embedder import ONNXSentenceEmbedder
            embedder = ONNXSentenceEmbedder(ONNX_INT8_PATH)
            _kw_model = KeyBERT(model=embedder)
            logger.info("SciBERT ONNX INT8 keyword model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load ONNX model, falling back: {e}")
            _kw_model = KeyBERT(model="all-MiniLM-L6-v2")
            logger.info("Fallback keyword model (all-MiniLM-L6-v2) loaded")
    else:
        logger.warning(
            f"SciBERT ONNX model not available at {ONNX_INT8_PATH}. "
            "Falling back to lightweight FastEmbed model."
        )
        _kw_model = KeyBERT(model="all-MiniLM-L6-v2")
        logger.info("Fallback keyword model (all-MiniLM-L6-v2) loaded")

    return _kw_model


_CS_AI_SEED_KEYWORDS = [
    # Core ML / DL foundations
    "machine learning", "deep learning", "neural network", "supervised learning",
    "unsupervised learning", "self-supervised learning", "semi-supervised learning",
    "reinforcement learning", "transfer learning", "contrastive learning",
    "meta-learning", "few-shot learning", "zero-shot learning", "continual learning",
    "curriculum learning", "active learning", "online learning", "representation learning",
    "metric learning", "multi-task learning", "federated learning",
    # Architectures & model types
    "transformer", "attention mechanism", "convolutional neural network",
    "recurrent neural network", "graph neural network", "variational autoencoder",
    "generative adversarial network", "diffusion model", "normalizing flow",
    "state space model", "mixture of experts", "neural architecture search",
    "capsule network", "memory network", "hypernetwork", "neural operator",
    # LLM & generative AI
    "large language model", "language model", "foundation model",
    "retrieval augmented generation", "prompt engineering", "in-context learning",
    "chain of thought", "instruction tuning", "alignment", "preference optimization",
    "fine-tuning", "parameter efficient fine-tuning", "model merging",
    "text generation", "code generation", "multimodal model", "vision language model",
    "world model", "tokenization", "decoding strategy",
    # Agents & reasoning
    "autonomous agent", "multi-agent system", "reasoning", "planning",
    "tool use", "function calling", "agentic workflow", "decision making",
    "causal reasoning", "commonsense reasoning", "logical reasoning",
    "neuro-symbolic", "program synthesis", "reward modeling",
    # NLP tasks
    "natural language processing", "text classification", "named entity recognition",
    "question answering", "information extraction", "information retrieval",
    "sentiment analysis", "machine translation", "summarization",
    "semantic parsing", "relation extraction", "coreference resolution",
    "dialogue system", "speech recognition", "text to speech",
    # Computer vision
    "computer vision", "image classification", "object detection",
    "semantic segmentation", "image generation", "video understanding",
    "visual question answering", "3d reconstruction", "point cloud",
    "optical flow", "depth estimation", "scene understanding",
    "image restoration", "super resolution",
    # Data & knowledge
    "knowledge graph", "knowledge distillation", "knowledge base",
    "vector database", "embedding", "semantic search", "dense retrieval",
    "data augmentation", "synthetic data", "dataset", "annotation",
    "feature engineering", "feature selection", "dimensionality reduction",
    # Training & optimization
    "optimization", "gradient descent", "batch normalization", "regularization",
    "dropout", "learning rate", "loss function", "backpropagation",
    "distributed training", "mixed precision", "model parallelism",
    "data parallelism", "convergence",
    # Efficiency & deployment
    "model compression", "quantization", "pruning", "distillation",
    "inference optimization", "edge computing", "on-device",
    "latency", "throughput", "scalability", "serving",
    # Safety, alignment & evaluation
    "benchmark", "evaluation", "robustness", "adversarial",
    "fairness", "bias", "interpretability", "explainability",
    "hallucination", "factuality", "safety", "red teaming",
    "watermarking", "copyright", "privacy", "differential privacy",
    # Applied / interdisciplinary ML
    "recommender system", "anomaly detection", "time series",
    "tabular data", "scientific computing", "drug discovery",
    "protein folding", "climate modeling", "robotics", "autonomous driving",
    "medical imaging", "electronic health record", "bioinformatics",
    # Infrastructure & systems
    "mlops", "model monitoring", "experiment tracking", "data pipeline",
    "feature store", "model registry", "continuous training",
]

_TECH_ABBREVS = {
    "ai", "ml", "dl", "nlp", "cv", "rl", "ir",
    "cnn", "rnn", "gnn", "vae", "gan", "ssm", "moe", "nas", "mlp",
    "llm", "rag", "rlhf", "dpo", "sft", "peft", "lora", "qlora", "icl", "cot",
    "bert", "gpt", "vit", "clip", "llama", "mamba", "rwkv", "t5",
    "api", "sdk", "gpu", "tpu", "cuda", "onnx", "mlops",
    "auc", "bleu", "rouge", "mmlu", "f1",
}

_TECH_BOOST = 1.3
_EMBEDDING_DEDUP_THRESHOLD = 0.92


def _is_technical(kw: str) -> bool:
    kw_lower = kw.lower()
    if kw_lower in _TECH_ABBREVS:
        return True
    return any(seed in kw_lower or kw_lower in seed for seed in _CS_AI_SEED_KEYWORDS)


def _deduplicate_substrings(candidates: list[tuple[str, float]]) -> list[tuple[str, float]]:
    kept: list[tuple[str, float]] = []
    for kw, score in candidates:
        kw_lower = kw.lower()
        dominated = False
        to_remove = None
        for i, (kept_kw, kept_score) in enumerate(kept):
            kept_lower = kept_kw.lower()
            if kw_lower in kept_lower and kept_score >= score:
                dominated = True
                break
            if kept_lower in kw_lower and score > kept_score:
                to_remove = i
                break
        if to_remove is not None:
            kept.pop(to_remove)
        if not dominated:
            kept.append((kw, score))
    return kept


def _embedding_deduplicate(
    candidates: list[tuple[str, float]],
    kw_model: KeyBERT,
) -> list[tuple[str, float]]:
    if len(candidates) <= 1:
        return candidates

    kws = [kw for kw, _ in candidates]
    embs = kw_model.model.embed(kws)
    norms = np.linalg.norm(embs, axis=1, keepdims=True).clip(min=1e-9)
    embs = embs / norms
    sim_matrix = embs @ embs.T

    kept_indices: list[int] = []
    suppressed: set[int] = set()

    for i in range(len(kws)):
        if i in suppressed:
            continue
        kept_indices.append(i)
        for j in range(i + 1, len(kws)):
            if j not in suppressed and sim_matrix[i, j] >= _EMBEDDING_DEDUP_THRESHOLD:
                suppressed.add(j)

    return [(candidates[i][0], candidates[i][1]) for i in kept_indices]


def extract_keywords(title: str, abstract: str, top_n: int = 10) -> list[str]:
    """Extract keywords from title + abstract with technical term prioritization and deduplication."""
    kw_model = get_keyword_model()
    text = f"{title}. {abstract[:1200]}"

    candidates = kw_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 3),
        stop_words="english",
        use_mmr=True,
        diversity=0.6,
        top_n=top_n * 2 + 5,
        seed_keywords=_CS_AI_SEED_KEYWORDS,
    )

    boosted = [
        (kw, score * _TECH_BOOST if _is_technical(kw) else score)
        for kw, score in candidates
    ]
    boosted.sort(key=lambda x: x[1], reverse=True)

    deduped = _deduplicate_substrings(boosted)
    deduped = _embedding_deduplicate(deduped, kw_model)

    deduped.sort(key=lambda x: x[1], reverse=True)
    return [kw for kw, _ in deduped[:top_n]]


def keywords_to_string(keywords: list[str]) -> str:
    return ", ".join(keywords)


def keywords_to_arxiv_query(keywords: list[str], max_terms: int = 6) -> str:
    """Build an AND-joined quoted query for the ArXiv API from extracted keywords."""
    terms = [f'"{kw}"' for kw in keywords[:max_terms]]
    return " AND ".join(terms)
