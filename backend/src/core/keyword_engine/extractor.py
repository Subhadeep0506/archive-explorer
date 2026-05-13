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
        logger.info(f"Loading SciBERT ONNX INT8 model from {ONNX_INT8_PATH}")
        from .onnx_embedder import ONNXSentenceEmbedder
        embedder = ONNXSentenceEmbedder(ONNX_INT8_PATH)
        _kw_model = KeyBERT(model=embedder)
        logger.info("SciBERT ONNX INT8 keyword model loaded successfully")
    else:
        logger.warning(
            f"SciBERT ONNX model not available at {ONNX_INT8_PATH}. "
            "Falling back to lightweight FastEmbed model."
        )
        _kw_model = KeyBERT(model="all-MiniLM-L6-v2")
        logger.info("Fallback keyword model (all-MiniLM-L6-v2) loaded")

    return _kw_model


def extract_keywords(title: str, abstract: str, top_n: int = 10) -> list[str]:
    """Extract keywords from title + abstract. Returns plain string list."""
    kw_model = get_keyword_model()
    text = f"{title}. {abstract[:1200]}"
    results = kw_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 3),
        stop_words="english",
        use_mmr=True,
        diversity=0.6,
        top_n=top_n,
    )
    return [kw for kw, _ in results]


def keywords_to_string(keywords: list[str]) -> str:
    return ", ".join(keywords)


def keywords_to_arxiv_query(keywords: list[str], max_terms: int = 6) -> str:
    """Build an AND-joined quoted query for the ArXiv API from extracted keywords."""
    terms = [f'"{kw}"' for kw in keywords[:max_terms]]
    return " AND ".join(terms)
