"""
ONNX SciBERT sentence embedder for KeyBERT keyword extraction.

Loads a pre-quantized SciBERT ONNX model from disk and mean-pools token
embeddings into fixed-size sentence vectors. Only the SciBERT tokenizer
config/vocab (~1 MB) is fetched from HuggingFace on first run and cached.
"""

import os
from pathlib import Path
from typing import List

import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer
from keybert.backend import BaseEmbedder

SCIBERT_TOKENIZER = "allenai/scibert_scivocab_uncased"


class ONNXSentenceEmbedder(BaseEmbedder):
    """
    KeyBERT-compatible embedder backed by a local ONNX model.
    Runs on CPU via ONNX Runtime with INT8 quantization — fast even on low-resource machines.
    """

    def __init__(self, onnx_path: Path, tokenizer_name: str = SCIBERT_TOKENIZER):
        super().__init__()
        num_threads = os.cpu_count() or 4
        sess_opts = ort.SessionOptions()
        sess_opts.execution_mode = ort.ExecutionMode.ORT_PARALLEL
        sess_opts.inter_op_num_threads = num_threads
        sess_opts.intra_op_num_threads = num_threads
        sess_opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        is_q4 = "q4" in onnx_path.stem.lower()
        disabled = ["SimplifiedLayerNormFusion"] if is_q4 else []
        self._ort_session = ort.InferenceSession(
            str(onnx_path), sess_options=sess_opts, disabled_optimizers=disabled
        )
        self._tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        input_names = {inp.name for inp in self._ort_session.get_inputs()}
        self._has_token_type_ids = "token_type_ids" in input_names

    def embed(self, documents: List[str], verbose: bool = False) -> np.ndarray:
        documents = [str(d) for d in documents]
        batch_size = 32
        all_embeddings: List[np.ndarray] = []

        for start in range(0, len(documents), batch_size):
            batch = documents[start : start + batch_size]
            encoded = self._tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="np",
            )

            feed = {
                "input_ids": encoded["input_ids"].astype(np.int64),
                "attention_mask": encoded["attention_mask"].astype(np.int64),
            }
            if self._has_token_type_ids:
                token_type_ids = encoded.get(
                    "token_type_ids", np.zeros_like(encoded["input_ids"])
                )
                feed["token_type_ids"] = token_type_ids.astype(np.int64)

            last_hidden = self._ort_session.run(None, feed)[0]

            mask = encoded["attention_mask"][:, :, np.newaxis].astype(np.float32)
            sum_emb = (last_hidden * mask).sum(axis=1)
            sum_mask = mask.sum(axis=1).clip(min=1e-9)
            all_embeddings.append(sum_emb / sum_mask)

        return np.vstack(all_embeddings)
