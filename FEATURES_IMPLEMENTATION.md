# ArxiverApp — Feature Implementation Guide

> **Audience**: Developer familiar with the existing codebase.
> **Stack**: FastAPI · SQLAlchemy (async) · PostgreSQL · Qdrant Cloud · LangChain (`QdrantVectorStore` for RAG, `CohereEmbeddings`) · LangGraph · SciBERT ONNX INT8 (keyword extraction) · Alembic · Pydantic v2
> **Conventions used in this document**
> - `src/model/foo.py` — SQLAlchemy model
> - `src/schema/foo.py` — Pydantic request/response schema
> - `src/router/foo.py` — FastAPI router
> - `src/controller/foo.py` — Business logic / DB layer
> - `src/core/<engine>/` — Core ML / LLM engines
> - All new migrations are created with `alembic revision --autogenerate -m "<message>"`

---

## Table of Contents

1. [Paper Recommendations](#1-paper-recommendations)
2. [Multi-Paper Cross-Chat](#2-multi-paper-cross-chat)
3. [Literature Review Generator](#3-literature-review-generator)
4. [Research Gap & Trend Analysis](#4-research-gap--trend-analysis)
5. [Smart ArXiv Alerts](#5-smart-arxiv-alerts)
6. [Collections / Reading Lists](#6-collections--reading-lists)
7. [Paper Annotations](#7-paper-annotations)
8. [Reading Progress & Status](#8-reading-progress--status)
9. [Keyword Extraction](#9-keyword-extraction)

---

## 1. ArXiv Catalog + Feed + Hybrid Recommendations

### Overview

Two stores: **PostgreSQL** for user data and catalog metadata (feed), **Qdrant Cloud** for all vector operations (recommendations + RAG). Qdrant's `cloud_inference=True` embeds catalog papers server-side — no local ML compute for the recommendation pipeline.

| Store | What lives there | Purpose |
|---|---|---|
| **PostgreSQL** | Users, saved papers, sessions, messages, profiles, settings, `arxiv_catalog` (metadata) | User data (ACID) + feed queries (ORDER BY + OFFSET/LIMIT) |
| **Qdrant `arxiv-papers`** | Catalog metadata + embeddings (server-side `intfloat/multilingual-e5-small`, 384-dim) | Recommendations: k-NN, on-topic, by-author |
| **Qdrant `paper-chunks`** | PDF chunk text + embeddings (Cohere `embed-v3`, 1024-dim) | RAG retrieval via `QdrantVectorStore` (replaces Pinecone) |

**Embeddings split:**
- **Catalog (recs):** Native `qdrant-client` with `cloud_inference=True` — embeds server-side via `Document()` objects. Zero local compute, zero Cohere calls. Lives in new `lib/qdrant.py`.
- **RAG chunks:** `core/vectorstore.py` updated — swap `PineconeVectorStore` → `QdrantVectorStore`. `core/embedding.py` (`EmbeddingFactory`) stays as-is. Same factory pattern used by `IngestionEngine` and `context_retriever_node` today.

**Thumbnails:** Client-side React components styled like HuggingFace model cards. No image generation or storage.

**Hybrid Recommendations** (per senior dev feedback):

| Signal | What it finds | Query type |
|---|---|---|
| Similar Papers | Semantically related papers across all categories | Qdrant k-NN via `Document()` (server-side embed) |
| On This Topic | Similar papers within the same category | Qdrant k-NN + `primary_category` payload filter |
| From These Authors | Other papers by the same authors | Qdrant scroll + `MatchText` payload filter on `authors` |
| Re-ranking | Boost by user history + recency | Python post-processing on combined results |

Validated prototype: `backend/utils/generate_recsys_vectorstore.py`.

---

### Step 1 — Dependencies

**Update file**: `requirements.txt`

```
qdrant-client>=1.12.0
langchain-qdrant>=0.2.0
sickle>=0.7.0
```

`langchain-cohere` is already installed (used by existing `EmbeddingFactory`). `cohere` is already present as a transitive dependency.

---

### Step 2 — Environment Variables [IGNORE]

**Update file**: `.env`

```
QDRANT_URI=https://your-cluster.cloud.qdrant.io:6333
QDRANT_API_KEY=...
```

`COHERE_API_KEY` already present — used by `EmbeddingFactory` via per-user decrypted keys.

---

### Step 3 — Qdrant Native Client (Recommendations)

**New file**: `src/lib/qdrant.py`

Follows the same pattern as other `lib/` clients (`ArxivClient`, `LangSearchClient`). Exposes:
- `get_qdrant_client()` — singleton native client with `cloud_inference=True` for server-side embedding
- `ensure_collections_exist()` — creates both collections on startup if missing

```python
import os
from qdrant_client import QdrantClient, models

CATALOG_COLLECTION  = "arxiv-papers"
CHUNKS_COLLECTION   = "paper-chunks"
CATALOG_EMBED_MODEL = "intfloat/multilingual-e5-small"  # 384-dim, server-side
CHUNKS_EMBED_DIM    = 1024                               # Cohere embed-v3

_client: QdrantClient | None = None

def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(
            url=os.environ["QDRANT_URI"],
            api_key=os.environ["QDRANT_API_KEY"],
            cloud_inference=True,
            check_compatibility=False,
        )
    return _client

def ensure_collections_exist() -> None:
    """Called once in lifespan startup. Creates arxiv-papers (recs) and paper-chunks (RAG) if missing."""
    # arxiv-papers: named vector with server-side inference, INT8 scalar quantization,
    #   text index on "authors" for MatchText queries
    # paper-chunks: regular 1024-dim vectors (Cohere embed-v3)
    ...
```

**Update file**: `main.py` — call `ensure_collections_exist()` in lifespan startup, after DB table creation.

---

### Step 4 — Update Existing Factories (Pinecone → Qdrant)

No new embedding or vectorstore files. Update the existing factories in `core/`:

**Update file**: `src/core/vectorstore.py`

Replace `PineconeVectorStore` with `QdrantVectorStore`. Same static factory pattern, same `build_vector_store(embedding_model)` signature. The `request` object is not needed here — `QDRANT_URI` and `QDRANT_API_KEY` come from env vars (not per-user keys).

```python
from langchain_qdrant import QdrantVectorStore
from ..lib.qdrant import get_qdrant_client, CHUNKS_COLLECTION

class VectorStoreFactory:
    @staticmethod
    def build_vector_store(embedding_model) -> QdrantVectorStore:
        return QdrantVectorStore(
            client=get_qdrant_client(),
            collection_name=CHUNKS_COLLECTION,
            embedding=embedding_model,
        )
```

**No change**: `src/core/embedding.py` — `EmbeddingFactory` already builds `CohereEmbeddings` with per-user API keys from `request.state.decrypted_api_keys["cohere"]`. Works as-is with the new vectorstore.

All existing callers (`IngestionEngine`, `context_retriever_node`, `SummaryEngine`) continue to work unchanged — they call `EmbeddingFactory.build_embedding_model()` then `VectorStoreFactory.build_vector_store()` exactly as before.

---

### Step 5 — ArXiv Catalog Model (PostgreSQL — metadata only, for feed)

**New file**: `src/model/arxiv_catalog.py`

Embeddings live in Qdrant. This table stores only metadata — used by the feed endpoint which needs `ORDER BY` + `OFFSET/LIMIT` (Qdrant can't sort by payload fields efficiently). Inherits from `Base, TimestampMixin` like all other models.

Columns: `id` (PK), `arxiv_id` (unique, indexed), `title`, `abstract` (Text), `authors`, `categories`, `primary_category` (indexed), `published_date`, `updated_date`, `pdf_url`, `paper_url`, `indexed_in_qdrant` (boolean, tracks Qdrant sync state, default `false`).

---

### Step 6 — Catalog Engine: OAI-PMH Harvest → PostgreSQL + Qdrant

Two-phase ingestion: metadata goes to PostgreSQL (for feed), then to Qdrant (for recommendations with server-side embedding). Based on `utils/fetch_arxiv_papers.py`.

**New file**: `src/core/catalog_engine/__init__.py` (empty)

**New file**: `src/core/catalog_engine/ingest.py`

Three functions:

- `load_catalog_from_oai(db, set_spec="cs", from_date=None, batch_size=500)` — Fetches records via `sickle.ListRecords()`, parses ArXiv XML (id, title, abstract, authors, categories, dates, urls), upserts to PostgreSQL in batches using `INSERT ... ON CONFLICT DO UPDATE` on `arxiv_id`.

- `upsert_catalog_to_qdrant(db, batch_size=100)` — Selects rows where `indexed_in_qdrant=False`, builds `PointStruct` with `Document(text=..., model=CATALOG_EMBED_MODEL)` for server-side embedding, calls `client.upsert()`, marks rows as indexed. Uses native `get_qdrant_client()` from `lib/qdrant.py`.

- `_parse_arxiv_record(record)` — Parses OAI-PMH XML into a dict matching `ArxivCatalog` columns. Same logic as existing `utils/fetch_arxiv_papers.py`.

**Initial load** (~300K papers, run once):

```bash
# load_catalog_from_oai(db, set_spec='cs', from_date='2021-01-01')
# upsert_catalog_to_qdrant(db)
```

PostgreSQL upsert: fast. Qdrant upsert with server-side embedding: bound by network I/O, not local compute.

---

### Step 7 — Daily Delta Update

**New file**: `src/core/catalog_engine/update.py`

`run_daily_catalog_update(db)` — calls `load_catalog_from_oai(db, from_date=yesterday)` then `upsert_catalog_to_qdrant(db)`. Returns `{new_records, indexed_in_qdrant}`.

---

### Step 8 — Schedule the Daily Update

**Update file**: `main.py` — add APScheduler cron job at 02:00 UTC calling `run_daily_catalog_update()` with a `session_pool()` session.

---

### Step 9 — Feed Endpoint (PostgreSQL Query)

Feed reads from PostgreSQL — `ORDER BY` + `OFFSET/LIMIT` pagination, which Qdrant cannot do on payload fields.

**New file**: `src/controller/catalog_controller.py`

`get_feed(topics, start, limit)` — `SELECT ... FROM arxiv_catalog WHERE primary_category IN (...) ORDER BY published_date DESC OFFSET/LIMIT`. Uses `session_pool()` like other controllers.

**Update file**: `src/router/arxiv.py` — add `GET /feed?topics=cs.AI,cs.LG&start=0&limit=20` endpoint.

---

### Step 10 — Thumbnail Cards (Client-Side)

No server-side image generation. Frontend React component renders a styled card per paper (gradient header by `primary_category`, title, authors, date). All data comes from feed endpoint metadata.

---

### Step 11 — Hybrid Recommendation Engine

Three retrieval signals + a re-ranking step. All use the **native Qdrant client** from `lib/qdrant.py` (not LangChain — these are recommendation queries, not RAG).

**New file**: `src/core/recommendation_engine/__init__.py` (empty)

**New file**: `src/core/recommendation_engine/recommender.py`

Four functions, all using `get_qdrant_client()` from `lib/qdrant.py`:

- `get_similar_papers(title, abstract, categories, exclude_ids, top_k=20)` — `client.query_points()` with `Document(text=..., model=CATALOG_EMBED_MODEL)` for server-side k-NN. Excludes already-saved paper IDs via `MatchAny` filter.

- `get_similar_on_topic(title, abstract, primary_category, exclude_ids, top_k=10)` — Same k-NN query + `FieldCondition(key="primary_category", match=MatchValue(...))` filter.

- `get_papers_by_authors(authors, exclude_ids, top_k=10)` — `client.scroll()` with `MatchText` filter on the `authors` text index. Iterates over first 5 author names, deduplicates results.

- `rerank_results(candidates, user_saved_categories)` — Python post-processing. Weights: 0.60 similarity + 0.15 category affinity + 0.15 recency + 0.10 reserved.

---

### Step 12 — Recommendation Controller + Router

**New file**: `src/controller/recommendation_controller.py`

`get_recommendations_for_paper(paper_id, user_id, limit)` — loads the paper from DB, collects user's saved paper IDs (for exclusion) and saved categories (for re-ranking), calls the three recommendation functions, re-ranks `similar_papers`, returns `{similar_papers, on_this_topic, from_these_authors}`. Uses `session_pool()` like other controllers.

**Update file**: `src/router/papers.py` — add `GET /{paper_id}/recommendations?limit=10`.

---

### Step 13 — RAG Ingestion (Pinecone → Qdrant)

Since `VectorStoreFactory` now returns `QdrantVectorStore` (Step 4), the existing `IngestionEngine` and `context_retriever_node` work with Qdrant without structural changes.

**Update file**: `src/core/ingest_engine/ingestion.py`

Minimal change — replace `PineconeVectorStore` type hint with `QdrantVectorStore`. The `ingest_paper_using_paper_id()` method already calls `VectorStoreFactory.build_vector_store()` → `vector_store.aadd_documents()`. For delete, replace Pinecone filter syntax (`{"paper_id": {"$in": paper_ids}}`) with Qdrant filter syntax (`models.Filter(must=[FieldCondition(...)])`).

**No change**: `src/core/chat_engine/agents/retriever.py`

The existing `context_retriever_node` already calls `EmbeddingFactory` → `VectorStoreFactory` → `vector_store.as_retriever()` with a `paper_id` filter. The only change is the filter syntax — Qdrant uses `models.Filter` with `FieldCondition` on `metadata.paper_id` instead of Pinecone's dict filter. The LangGraph pipeline, streaming, and conversation history logic remain untouched.

---

### Step 14 — Background Task (Keyword Extraction Only)

**New file**: `src/core/background_tasks.py`

`index_paper_background(paper_id, title, abstract)` — runs SciBERT ONNX INT8 keyword extraction (~80ms–2s) via `extract_keywords()`, writes result to `Paper.keywords` using `session_pool()`. No catalog vector store write — catalog is pre-indexed in Qdrant. RAG chunk ingestion is a separate step triggered by the existing ingestion flow.

---

### Step 15 — Schemas

**Update file**: `src/schema/paper.py` — add `RecommendationItem` (arxiv_id, title, authors, categories, score, final_score) and `RecommendationsResponse` (similar_papers, on_this_topic, from_these_authors lists).

---

### Step 16 — Migration

```bash
alembic revision --autogenerate -m "add arxiv_catalog table"
alembic revision --autogenerate -m "add keywords to paper"
alembic upgrade head
```

---

### Summary of the Full Flow

```
Initial load (run once):
  OAI-PMH 5yr harvest → PostgreSQL (metadata)
  Then: upsert_catalog_to_qdrant() → Qdrant server-side embedding
  ~300K papers. No local ML compute. No Cohere calls.

Daily (02:00 UTC, APScheduler):
  OAI-PMH delta (from=yesterday)
    ├─ PostgreSQL upsert (metadata for feed)
    └─ Qdrant upsert (server-side embedding for recs)
    ~500–2000 new papers

User opens feed:
  GET /api/v1/arxiv/feed?topics=cs.AI,cs.LG&limit=20
    └─ PostgreSQL: SELECT ... WHERE primary_category IN (...) ORDER BY published_date DESC
       Frontend renders thumbnail cards from metadata

User saves paper:
  POST /api/v1/papers → 201 Created
    ├─ BackgroundTask: keyword extraction (SciBERT ONNX)         ~80ms–2s
    └─ IngestionEngine → VectorStoreFactory (QdrantVectorStore)  ~10–30s
       Same EmbeddingFactory + VectorStoreFactory pattern as today

User opens paper page — hybrid recommendations (native qdrant-client):
  GET /api/v1/papers/{id}/recommendations
    ├─ "Similar Papers"       → query_points(Document())  ~50ms  (server-side embed)
    ├─ "On This Topic"        → query_points + filter     ~50ms  (server-side embed)
    ├─ "From These Authors"   → scroll + MatchText        ~30ms  (payload filter)
    └─ Re-rank with user history (category affinity + recency)

User chats about a paper (RAG):
  context_retriever_node → EmbeddingFactory → VectorStoreFactory
    └─ Same LangGraph pipeline, QdrantVectorStore replaces PineconeVectorStore
```

---

---

## 2. Multi-Paper Cross-Chat

### Overview

Currently `Session.paper_id` is a single FK. Multi-paper chat lets a user start a session tied to **multiple papers** and ask questions across all of them. The retriever queries Qdrant's `paper-chunks` collection filtered by a list of `paper_ids` instead of one, and the LLM receives combined context from all papers.

---

### Step 1 — New Join Table Model

**New file**: `src/model/session_paper.py` — `session_paper` association table (`session_id` FK, `paper_id` FK, both PKs with `ondelete="CASCADE"`).

---

### Step 2 — Update the Session Model

**Update file**: `src/model/chat_session.py` — add `papers: Mapped[list["Paper"]]` many-to-many relationship via `session_paper_association`. Keep existing `paper_id` FK for single-paper backward compat. When `paper_id` is NULL and `papers` list is populated → multi-paper session.

---

### Step 3 — Update AgentState

**Update file**: `src/core/chat_engine/agent_state.py` — add `paper_ids: list[str]` and `paper_titles: str`. Defaults to `[paper_id]` for single-paper sessions.

---

### Step 4 — Update the Retriever Node

**Update file**: `src/core/chat_engine/agents/retriever.py`

The existing `context_retriever_node` already calls `EmbeddingFactory` → `VectorStoreFactory` → `vector_store.as_retriever()`. The only change for multi-paper: resolve `paper_ids = state.get("paper_ids") or [state["paper_id"]]` and pass a Qdrant `Filter` with `MatchAny` on `metadata.paper_id` instead of the current single `{"paper_id": state["paper_id"]}` dict filter. All streaming, conversation history, and doc extraction logic stays the same.

---

### Step 5 — Update Chat Schema

**Update file**: `src/schema/chat.py` — add `paper_ids: Optional[list[int]] = None` to `ChatQueryRequest` alongside existing `paper_id`. In the chat controller, if `paper_ids` is provided, set `state["paper_ids"]` and leave `state["paper_id"]` as the first element for backward compat.

---

### Step 6 — Update the Session Controller

**Update file**: `src/controller/session_controller.py` — add `create_multi_paper_session(user_id, paper_ids, title)`. Validates all paper_ids belong to user, creates Session with `paper_id=None`, assigns `session.papers` relationship. Uses `session_pool()`.

---

### Step 7 — Update the Session Router

**Update file**: `src/router/sessions.py` — add `POST /multi` endpoint accepting `{paper_ids: list[int], title: str}`.

---

### Step 8 — Database Migration

```bash
alembic revision --autogenerate -m "add session_paper association table"
alembic upgrade head
```

---

---

## 3. Literature Review Generator

### Overview

Given a list of paper IDs from the user's library, generate a structured literature review with sections: **Background**, **Methodology Comparison**, **Key Findings**, **Identified Gaps**, **Future Directions**. Reuses `SummaryEngine` logic: retrieve chunks from Qdrant's `paper-chunks` collection for each paper, then run a multi-step LLM synthesis.

---

### Step 1 — Create the Literature Review Engine

**New file**: `src/core/lit_review_engine/lit_review.py`

`LitReviewEngine` static class (same pattern as `SummaryEngine`):

- `generate(paper_ids, paper_titles, request)` — For each paper, retrieves chunks via `VectorStoreFactory` with `paper_id` filter (k=200), concatenates per paper (capped at 4096 tokens each). If combined > 32768 tokens, generates intermediate summaries via `SummaryEngine`. Final call to `LLMFactory.build_llm("groq/qwen3-32b")` with `LIT_REVIEW_SYSTEM_PROMPT`.

---

### Step 2 — Add the Prompt

**Update file**: `src/config/prompts.py` — add `LIT_REVIEW_SYSTEM_PROMPT` with sections: Background, Methodology Comparison, Key Findings, Identified Gaps, Future Directions.

---

### Step 3 — Schema, Controller, Router

**Update file**: `src/schema/paper.py` — add `LitReviewRequest(paper_ids, title)` and `LitReviewResponse(title, content, paper_ids, paper_titles)`.

**New file**: `src/controller/lit_review_controller.py` — `generate_literature_review()` validates ownership + ingested state, calls `LitReviewEngine.generate()`. Uses `session_pool()`.

**New file**: `src/router/lit_review.py` — `POST /literature-review/` with `Depends(get_current_user)` and `Depends(load_user_api_keys)`.

---

### Step 6 — Register Router

**Update file**: `main.py`

```python
from src.router.lit_review import router as lit_review_router
app.include_router(lit_review_router, prefix="/api/v1")
```

### Step 7 — No Migration Needed

Literature reviews are generated on-demand. If you want to persist them later, add a `LiteratureReview` table (id, user_id, title, content, paper_ids JSONB, created_at). That is optional for a first iteration.

---

---

## 4. Research Gap & Trend Analysis

### Overview

A pure analytics feature over existing data. Produces two outputs:

- **Trend report**: How the `new_tech_applicability` tags and `topics` in the user's library have evolved over `published_date`, showing which areas are growing vs. stagnating.
- **Gap report**: Sub-topics present in `topic_preferences` or library topics that have not appeared in any saved paper in the last N months, flagged as potential gaps.

No LLM is required; this is computed from structured fields already in PostgreSQL.

---

### Step 1 — Create the Analytics Engine

**New file**: `src/core/analytics_engine/__init__.py` (empty)

**New file**: `src/core/analytics_engine/trends.py`

```python
from collections import defaultdict, Counter
from datetime import datetime, timedelta

def compute_tech_trends(papers_with_usability: list[dict]) -> dict:
    """
    Input: list of dicts, each containing:
      {
        "published_date": "2023-05-12",   # from Paper.published_date
        "new_tech_applicability": {        # from Usability.new_tech_applicability
            "LLMs": true, "RAG": true, ...
        },
        "topics": "cs.AI cs.LG"           # from Paper.topics
      }

    Algorithm:
    1. Group papers by year-month (YYYY-MM) using published_date.
    2. For each month, count how many papers have each tech tag set to True.
    3. Compute month-over-month delta for each tag.
    4. Return a dict:
       {
         "timeline": {
           "2023-01": {"LLMs": 2, "RAG": 1, ...},
           "2023-02": {"LLMs": 4, "RAG": 3, ...},
         },
         "trending_up": ["LLMs", "RAG"],   # tags growing in last 3 months
         "trending_down": ["CV"],           # tags declining
         "top_tags": [("LLMs", 12), ...],  # sorted by total count
       }
    """

def compute_research_gaps(
    papers_with_usability: list[dict],
    topic_preferences: list[str],
    gap_window_months: int = 6,
) -> dict:
    """
    Algorithm:
    1. Build a set of all topics in saved papers (split Paper.topics on spaces).
    2. Find the most recent published_date for each topic.
    3. A topic is a "gap" if:
       - It is in topic_preferences OR in any saved paper's topics, AND
       - No paper with that topic has been saved in the last `gap_window_months`.
    4. Return:
       {
         "gaps": [
           {"topic": "cs.RO", "last_seen": "2022-11", "months_since": 18},
           ...
         ],
         "active_topics": ["cs.AI", "cs.LG"],
       }
    """
```

---

### Step 2 — Create the Controller

**New file**: `src/controller/analytics_controller.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from src.model.paper import Paper
from src.model.usability import Usability
from src.model.profile import Profile
from src.core.analytics_engine.trends import compute_tech_trends, compute_research_gaps

async def get_trend_analysis(user_id: int, db: AsyncSession) -> dict:
    """
    1. Query papers with their usabilities using joinedload:
         SELECT paper.*, usability.*
         FROM paper
         LEFT JOIN usability ON usability.paper_id = paper.id
                             AND usability.user_id = paper.user_id
         WHERE paper.user_id = :user_id

    2. Build papers_with_usability list of dicts from query results.
       For papers with no Usability row, use empty dicts for JSON fields.

    3. Call compute_tech_trends(papers_with_usability) -> trends

    4. Return {"trends": trends, "paper_count": len(papers)}
    """

async def get_gap_analysis(user_id: int, gap_months: int, db: AsyncSession) -> dict:
    """
    1. Same query as above to get papers + usabilities.
    2. Query Profile.topic_preferences for user_id.
    3. Call compute_research_gaps(
           papers_with_usability,
           topic_preferences=profile.topic_preferences or [],
           gap_window_months=gap_months,
       ) -> gaps

    4. Return {"gaps": gaps, "analyzed_months": gap_months}
    """
```

---

### Step 3 — Create the Schema

**New file**: `src/schema/analytics.py`

```python
from pydantic import BaseModel
from typing import Optional

class TechTrendPoint(BaseModel):
    month: str           # "YYYY-MM"
    counts: dict[str, int]  # tag -> count

class TrendAnalysisResponse(BaseModel):
    timeline: list[TechTrendPoint]
    trending_up: list[str]
    trending_down: list[str]
    top_tags: list[tuple[str, int]]
    paper_count: int

class GapItem(BaseModel):
    topic: str
    last_seen: Optional[str]   # "YYYY-MM" or None if never seen
    months_since: Optional[int]

class GapAnalysisResponse(BaseModel):
    gaps: list[GapItem]
    active_topics: list[str]
    analyzed_months: int
```

---

### Step 4 — Create the Router

**New file**: `src/router/analytics.py`

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db
from src.lib.auth import get_current_user
from src.controller.analytics_controller import get_trend_analysis, get_gap_analysis
from src.schema.analytics import TrendAnalysisResponse, GapAnalysisResponse

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/trends", response_model=TrendAnalysisResponse)
async def tech_trends_endpoint(
    user_id: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns technology trend data derived from the user's paper library."""
    return await get_trend_analysis(user_id=user_id, db=db)

@router.get("/gaps", response_model=GapAnalysisResponse)
async def research_gaps_endpoint(
    months: int = Query(default=6, ge=1, le=24),
    user_id: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns topics that haven't had new papers saved in the last N months."""
    return await get_gap_analysis(user_id=user_id, gap_months=months, db=db)
```

---

### Step 5 — Register Router

**Update file**: `main.py`

```python
from src.router.analytics import router as analytics_router
app.include_router(analytics_router, prefix="/api/v1")
```

### Step 6 — No Migration Needed

All data is read from existing `Paper`, `Usability`, and `Profile` tables.

---

---

## 5. Smart ArXiv Alerts

### Overview

A background job that runs daily (or on-demand) and checks ArXiv for new papers matching the user's `topic_preferences`. New papers (not yet in the user's library) are stored in an `Alert` table. The user can view and dismiss alerts from a dedicated endpoint. A future iteration can email these alerts.

---

### Step 1 — New Database Model

**New file**: `src/model/alert.py`

```python
from sqlalchemy import ForeignKey, String, Boolean, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.db import Base, TimestampMixin

class Alert(Base, TimestampMixin):
    """Stores new ArXiv paper alerts for users."""

    __tablename__ = "alert"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"),
                                          nullable=False, index=True)
    arxiv_id: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    abstract: Mapped[str] = mapped_column(String, nullable=False)
    authors: Mapped[str] = mapped_column(String(512), nullable=False)
    pdf_url: Mapped[str | None] = mapped_column(String, nullable=True)
    paper_url: Mapped[str | None] = mapped_column(String, nullable=True)
    categories: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'"))
    published_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    dismissed: Mapped[bool] = mapped_column(Boolean, nullable=False,
                                             server_default=text("false"), default=False)
    saved: Mapped[bool] = mapped_column(Boolean, nullable=False,
                                         server_default=text("false"), default=False)

    user: Mapped["User"] = relationship("User")
```

**Update file**: `src/model/user.py`

Add the relationship:

```python
alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="user",
                                               cascade="all, delete-orphan")
```

---

### Step 2 — Create the Alert Job

**New file**: `src/core/alert_engine/__init__.py` (empty)

**New file**: `src/core/alert_engine/alert_job.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.model.paper import Paper
from src.model.alert import Alert
from src.model.profile import Profile
from src.lib.arxiv import ArxivClient

async def run_alert_job_for_user(user_id: int, db: AsyncSession) -> int:
    """
    Checks ArXiv for new papers matching user's topic preferences.
    Returns the count of new alerts created.

    Algorithm:
    1. Query Profile.topic_preferences for user_id.
       If empty, return 0 (no preferences set — nothing to alert on).

    2. Query all existing Paper.arxiv_ids for user_id (saved papers).
       Also query all Alert.arxiv_ids for user_id (already alerted papers).
       Build a combined exclusion set.

    3. Call ArxivClient().feed_by_topics(
           topics=topic_preferences,
           max_results=30,
           sort_by="submittedDate",
           sort_order="descending",
       )

    4. Filter results:
       - Exclude any result whose arxiv_id is in the exclusion set.
       - Only include papers published within the last 7 days
         (compare result["published"] to datetime.utcnow() - timedelta(days=7)).

    5. For each remaining result, create an Alert row:
         Alert(
             user_id=user_id,
             arxiv_id=result["arxiv_id"],
             title=result["title"],
             abstract=result["abstract"],
             authors=", ".join(result["authors"]),
             pdf_url=result["pdf_url"],
             paper_url=result["paper_url"],
             categories=result["categories"],
             published_date=result["published"],
         )

    6. db.add_all(new_alerts), await db.commit()
    7. Return len(new_alerts)
    """

async def run_alert_job_for_all_users(db: AsyncSession) -> dict:
    """
    Runs run_alert_job_for_user for every user in the system.
    Intended to be called by a cron/scheduler.
    Returns {"users_processed": N, "total_alerts_created": M}
    """
    from src.model.user import User
    result = await db.execute(select(User.id))
    user_ids = result.scalars().all()
    total = 0
    for uid in user_ids:
        total += await run_alert_job_for_user(uid, db)
    return {"users_processed": len(user_ids), "total_alerts_created": total}
```

---

### Step 3 — Schedule the Job

**Update file**: `main.py`

Use `apscheduler` (add to `requirements.txt`: `apscheduler>=3.10`).

Inside the `lifespan` context manager (after the existing startup code):

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.core.alert_engine.alert_job import run_alert_job_for_all_users

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job("cron", hour=6, minute=0)   # runs daily at 06:00 UTC
async def daily_alert_job():
    async with get_db_session() as db:  # use your existing session factory
        await run_alert_job_for_all_users(db)

scheduler.start()
```

Stop the scheduler on shutdown: `scheduler.shutdown()` in the teardown section of the lifespan.

---

### Step 4 — Create the Controller

**New file**: `src/controller/alert_controller.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from src.model.alert import Alert
from src.core.alert_engine.alert_job import run_alert_job_for_user

async def get_user_alerts(
    user_id: int, include_dismissed: bool, db: AsyncSession
) -> list[Alert]:
    """
    SELECT * FROM alert
    WHERE user_id = :user_id
      AND (:include_dismissed OR dismissed = false)
    ORDER BY created_at DESC
    """

async def dismiss_alert(alert_id: int, user_id: int, db: AsyncSession) -> Alert:
    """
    UPDATE alert SET dismissed = true
    WHERE id = :alert_id AND user_id = :user_id
    Return updated alert. Raise 404 if not found.
    """

async def dismiss_all_alerts(user_id: int, db: AsyncSession) -> int:
    """
    UPDATE alert SET dismissed = true
    WHERE user_id = :user_id AND dismissed = false
    Return count of updated rows.
    """

async def trigger_alert_job(user_id: int, db: AsyncSession) -> int:
    """Manual trigger for a single user. Returns count of new alerts."""
    return await run_alert_job_for_user(user_id, db)
```

---

### Step 5 — Create the Schema

**New file**: `src/schema/alert.py`

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AlertResponse(BaseModel):
    id: int
    arxiv_id: str
    title: str
    abstract: str
    authors: str
    pdf_url: Optional[str]
    paper_url: Optional[str]
    categories: list[str]
    published_date: Optional[str]
    dismissed: bool
    saved: bool
    created_at: datetime

    class Config:
        from_attributes = True

class AlertListResponse(BaseModel):
    alerts: list[AlertResponse]
    total: int
    unread_count: int
```

---

### Step 6 — Create the Router

**New file**: `src/router/alerts.py`

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db
from src.lib.auth import get_current_user
from src.controller.alert_controller import (
    get_user_alerts, dismiss_alert, dismiss_all_alerts, trigger_alert_job
)
from src.schema.alert import AlertListResponse, AlertResponse

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("/", response_model=AlertListResponse)
async def get_alerts(
    include_dismissed: bool = Query(default=False),
    user_id: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all alerts for the current user."""
    alerts = await get_user_alerts(user_id, include_dismissed, db)
    unread = sum(1 for a in alerts if not a.dismissed)
    return AlertListResponse(alerts=alerts, total=len(alerts), unread_count=unread)

@router.post("/refresh", response_model=dict)
async def refresh_alerts(
    user_id: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger the alert job for the current user."""
    count = await trigger_alert_job(user_id, db)
    return {"new_alerts": count}

@router.patch("/{alert_id}/dismiss", response_model=AlertResponse)
async def dismiss_single_alert(
    alert_id: int,
    user_id: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await dismiss_alert(alert_id, user_id, db)

@router.patch("/dismiss-all", response_model=dict)
async def dismiss_all(
    user_id: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await dismiss_all_alerts(user_id, db)
    return {"dismissed_count": count}
```

---

### Step 7 — Register Router

**Update file**: `main.py`

```python
from src.router.alerts import router as alerts_router
app.include_router(alerts_router, prefix="/api/v1")
```

---

### Step 8 — Migration

```bash
alembic revision --autogenerate -m "add alert table"
alembic upgrade head
```

---

---

## 6. Collections / Reading Lists

### Overview

Users can create named collections (e.g. "Thesis Research", "Interview Prep") and assign any of their saved papers to them. A paper can belong to multiple collections. Collections are user-scoped.

---

### Step 1 — New Models

**New file**: `src/model/collection.py`

```python
from sqlalchemy import ForeignKey, String, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.db import Base, TimestampMixin

# Association table (no extra columns needed)
collection_paper = Table(
    "collection_paper",
    Base.metadata,
    Column("collection_id", ForeignKey("collection.id", ondelete="CASCADE"), primary_key=True),
    Column("paper_id",      ForeignKey("paper.id",      ondelete="CASCADE"), primary_key=True),
)

class Collection(Base, TimestampMixin):
    """A named group of papers belonging to a user."""

    __tablename__ = "collection"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"),
                                          nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="collections")
    papers: Mapped[list["Paper"]] = relationship(
        "Paper", secondary=collection_paper, backref="collections"
    )
```

**Update file**: `src/model/user.py`

```python
collections: Mapped[list["Collection"]] = relationship(
    "Collection", back_populates="user", cascade="all, delete-orphan"
)
```

---

### Step 2 — Create the Schema

**New file**: `src/schema/collection.py`

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from src.schema.paper import PaperResponse  # existing response schema

class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = None

class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class CollectionResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str]
    paper_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CollectionDetailResponse(CollectionResponse):
    papers: list[PaperResponse]

class AddPapersToCollectionRequest(BaseModel):
    paper_ids: list[int]

class RemovePapersFromCollectionRequest(BaseModel):
    paper_ids: list[int]
```

---

### Step 3 — Create the Controller

**New file**: `src/controller/collection_controller.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.model.collection import Collection
from src.model.paper import Paper
from src.errors import NotFoundError, ForbiddenError  # existing error classes

async def create_collection(user_id: int, name: str, description: str | None,
                             db: AsyncSession) -> Collection:
    """INSERT INTO collection (user_id, name, description) VALUES (...). Return new row."""

async def get_user_collections(user_id: int, db: AsyncSession) -> list[Collection]:
    """
    SELECT collection.*, COUNT(collection_paper.paper_id) as paper_count
    FROM collection
    LEFT JOIN collection_paper ON collection.id = collection_paper.collection_id
    WHERE collection.user_id = :user_id
    GROUP BY collection.id
    ORDER BY collection.created_at DESC
    """

async def get_collection_detail(collection_id: int, user_id: int,
                                  db: AsyncSession) -> Collection:
    """
    SELECT * FROM collection WHERE id = :collection_id
    Use selectinload(Collection.papers) to eager-load papers.
    Raise NotFoundError if not found, ForbiddenError if user_id doesn't match.
    """

async def update_collection(collection_id: int, user_id: int,
                              name: str | None, description: str | None,
                              db: AsyncSession) -> Collection:
    """UPDATE collection SET ... WHERE id=:id AND user_id=:user_id"""

async def delete_collection(collection_id: int, user_id: int,
                              db: AsyncSession) -> None:
    """DELETE FROM collection WHERE id=:id AND user_id=:user_id"""

async def add_papers_to_collection(collection_id: int, paper_ids: list[int],
                                    user_id: int, db: AsyncSession) -> Collection:
    """
    1. Verify collection belongs to user_id.
    2. Verify all paper_ids belong to user_id.
    3. Load the Collection with its papers relationship.
    4. Append Paper objects not already in collection.papers.
    5. Commit and return updated collection.
    """

async def remove_papers_from_collection(collection_id: int, paper_ids: list[int],
                                          user_id: int, db: AsyncSession) -> Collection:
    """
    1. Verify collection belongs to user_id.
    2. Load collection.papers.
    3. Remove papers whose id is in paper_ids.
    4. Commit and return updated collection.
    """
```

---

### Step 4 — Create the Router

**New file**: `src/router/collections.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db
from src.lib.auth import get_current_user
from src.controller.collection_controller import (
    create_collection, get_user_collections, get_collection_detail,
    update_collection, delete_collection,
    add_papers_to_collection, remove_papers_from_collection,
)
from src.schema.collection import (
    CollectionCreate, CollectionUpdate, CollectionResponse,
    CollectionDetailResponse, AddPapersToCollectionRequest,
    RemovePapersFromCollectionRequest,
)

router = APIRouter(prefix="/collections", tags=["Collections"])

@router.get("/", response_model=list[CollectionResponse])
async def list_collections(user_id=Depends(get_current_user), db=Depends(get_db)):
    return await get_user_collections(user_id, db)

@router.post("/", response_model=CollectionResponse, status_code=201)
async def create_collection_endpoint(
    payload: CollectionCreate, user_id=Depends(get_current_user), db=Depends(get_db)
):
    return await create_collection(user_id, payload.name, payload.description, db)

@router.get("/{collection_id}", response_model=CollectionDetailResponse)
async def get_collection(collection_id: int, user_id=Depends(get_current_user), db=Depends(get_db)):
    return await get_collection_detail(collection_id, user_id, db)

@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection_endpoint(
    collection_id: int, payload: CollectionUpdate,
    user_id=Depends(get_current_user), db=Depends(get_db)
):
    return await update_collection(collection_id, user_id, payload.name, payload.description, db)

@router.delete("/{collection_id}", status_code=204)
async def delete_collection_endpoint(
    collection_id: int, user_id=Depends(get_current_user), db=Depends(get_db)
):
    await delete_collection(collection_id, user_id, db)

@router.post("/{collection_id}/papers", response_model=CollectionDetailResponse)
async def add_papers(
    collection_id: int, payload: AddPapersToCollectionRequest,
    user_id=Depends(get_current_user), db=Depends(get_db)
):
    return await add_papers_to_collection(collection_id, payload.paper_ids, user_id, db)

@router.delete("/{collection_id}/papers", response_model=CollectionDetailResponse)
async def remove_papers(
    collection_id: int, payload: RemovePapersFromCollectionRequest,
    user_id=Depends(get_current_user), db=Depends(get_db)
):
    return await remove_papers_from_collection(collection_id, payload.paper_ids, user_id, db)
```

---

### Step 5 — Register Router

**Update file**: `main.py`

```python
from src.router.collections import router as collections_router
app.include_router(collections_router, prefix="/api/v1")
```

---

### Step 6 — Migration

```bash
alembic revision --autogenerate -m "add collection and collection_paper tables"
alembic upgrade head
```

---

---

## 7. Paper Annotations

### Overview

Users can highlight text from a paper and attach a note to it (like a sticky note). Annotations are scoped to a user + paper + page. The RAG chat can optionally include the user's annotations as additional context when answering questions about that paper.

---

### Step 1 — New Database Model

**New file**: `src/model/annotation.py`

```python
from sqlalchemy import ForeignKey, String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.db import Base, TimestampMixin

class Annotation(Base, TimestampMixin):
    """User highlight + note on a specific page of a paper."""

    __tablename__ = "annotation"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"),
                                          nullable=False, index=True)
    paper_id: Mapped[int] = mapped_column(ForeignKey("paper.id", ondelete="CASCADE"),
                                           nullable=False, index=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    highlighted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True, default="yellow")

    user: Mapped["User"] = relationship("User")
    paper: Mapped["Paper"] = relationship("Paper", back_populates="annotations")
```

**Update file**: `src/model/paper.py`

```python
annotations: Mapped[list["Annotation"]] = relationship(
    "Annotation", back_populates="paper", cascade="all, delete-orphan"
)
```

---

### Step 2 — Create the Schema

**New file**: `src/schema/annotation.py`

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AnnotationCreate(BaseModel):
    paper_id: int
    page_number: Optional[int] = None
    highlighted_text: Optional[str] = None
    note: Optional[str] = None
    color: Optional[str] = "yellow"

class AnnotationUpdate(BaseModel):
    note: Optional[str] = None
    color: Optional[str] = None

class AnnotationResponse(BaseModel):
    id: int
    user_id: int
    paper_id: int
    page_number: Optional[int]
    highlighted_text: Optional[str]
    note: Optional[str]
    color: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

---

### Step 3 — Create the Controller

**New file**: `src/controller/annotation_controller.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.model.annotation import Annotation
from src.errors import NotFoundError

async def create_annotation(user_id: int, paper_id: int, page_number: int | None,
                              highlighted_text: str | None, note: str | None,
                              color: str, db: AsyncSession) -> Annotation:
    """
    Validate the paper belongs to user_id first.
    INSERT INTO annotation (...). Return new row.
    """

async def get_annotations_for_paper(user_id: int, paper_id: int,
                                      db: AsyncSession) -> list[Annotation]:
    """
    SELECT * FROM annotation
    WHERE user_id=:user_id AND paper_id=:paper_id
    ORDER BY page_number ASC NULLS LAST, created_at ASC
    """

async def update_annotation(annotation_id: int, user_id: int,
                              note: str | None, color: str | None,
                              db: AsyncSession) -> Annotation:
    """
    UPDATE annotation SET note=:note, color=:color
    WHERE id=:annotation_id AND user_id=:user_id
    Raise NotFoundError if not found.
    """

async def delete_annotation(annotation_id: int, user_id: int,
                              db: AsyncSession) -> None:
    """
    DELETE FROM annotation WHERE id=:annotation_id AND user_id=:user_id
    """

async def get_annotation_context_for_rag(
    paper_id: int, user_id: int, db: AsyncSession
) -> str:
    """
    Called by the chat controller when building the RAG context.
    Fetches all annotations for paper+user and formats them as:
      '=== User Annotations ===
       [Page 3] "...highlighted text..." — Note: user's note
       [Page 7] "..." — Note: ...'
    Returns empty string if no annotations exist.
    """
```

---

### Step 4 — Inject Annotations into the RAG Pipeline (Optional)

**Update file**: `src/core/chat_engine/agents/generate.py`

In `generate_response_node`, after building `document_context`, append annotation context if present:

```python
annotation_context = state.get("annotation_context", "")
if annotation_context:
    document_context += f"\n\n{annotation_context}"
```

**Update file**: `src/core/chat_engine/agent_state.py`

Add to `AgentState`:

```python
annotation_context: str  # pre-fetched by the chat controller before graph invocation
```

**Update file**: `src/controller/chat_controller.py`

Before invoking the LangGraph graph, fetch annotation context:

```python
from src.controller.annotation_controller import get_annotation_context_for_rag

annotation_context = await get_annotation_context_for_rag(paper_id, user_id, db)
# Pass it in the initial state dict when calling graph.ainvoke(...)
```

---

### Step 5 — Create the Router

**New file**: `src/router/annotations.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db
from src.lib.auth import get_current_user
from src.controller.annotation_controller import (
    create_annotation, get_annotations_for_paper,
    update_annotation, delete_annotation,
)
from src.schema.annotation import (
    AnnotationCreate, AnnotationUpdate, AnnotationResponse
)

router = APIRouter(prefix="/annotations", tags=["Annotations"])

@router.post("/", response_model=AnnotationResponse, status_code=201)
async def create(payload: AnnotationCreate, user_id=Depends(get_current_user),
                  db=Depends(get_db)):
    return await create_annotation(
        user_id, payload.paper_id, payload.page_number,
        payload.highlighted_text, payload.note, payload.color or "yellow", db
    )

@router.get("/paper/{paper_id}", response_model=list[AnnotationResponse])
async def get_for_paper(paper_id: int, user_id=Depends(get_current_user),
                         db=Depends(get_db)):
    return await get_annotations_for_paper(user_id, paper_id, db)

@router.put("/{annotation_id}", response_model=AnnotationResponse)
async def update(annotation_id: int, payload: AnnotationUpdate,
                  user_id=Depends(get_current_user), db=Depends(get_db)):
    return await update_annotation(annotation_id, user_id, payload.note, payload.color, db)

@router.delete("/{annotation_id}", status_code=204)
async def delete(annotation_id: int, user_id=Depends(get_current_user),
                  db=Depends(get_db)):
    await delete_annotation(annotation_id, user_id, db)
```

---

### Step 6 — Register Router

**Update file**: `main.py`

```python
from src.router.annotations import router as annotations_router
app.include_router(annotations_router, prefix="/api/v1")
```

---

### Step 7 — Migration

```bash
alembic revision --autogenerate -m "add annotation table"
alembic upgrade head
```

---

---

## 8. Reading Progress & Status

### Overview

Add a `reading_status` field to the `Paper` model so users can track where they are with each paper. Status values: `UNREAD`, `READING`, `COMPLETED`, `ARCHIVED`. This is a minimal one-field change that enables library filtering and progress views.

---

### Step 1 — Add the Enum

**Update file**: `src/lib/enum.py`

```python
from enum import Enum

class ReadingStatusEnum(str, Enum):
    UNREAD    = "UNREAD"
    READING   = "READING"
    COMPLETED = "COMPLETED"
    ARCHIVED  = "ARCHIVED"
```

---

### Step 2 — Update the Paper Model

**Update file**: `src/model/paper.py`

Add one import and one field:

```python
from src.lib.enum import PaperSourceEnum, ReadingStatusEnum  # add ReadingStatusEnum

class Paper(Base, TimestampMixin):
    # ... existing fields ...

    reading_status: Mapped[str] = mapped_column(
        SQLAlchemyEnum(ReadingStatusEnum, native_enum=False, length=20),
        nullable=False,
        server_default=ReadingStatusEnum.UNREAD.value,
        default=ReadingStatusEnum.UNREAD.value,
    )
```

---

### Step 3 — Update the Paper Schema

**Update file**: `src/schema/paper.py`

Add `reading_status` to `PaperResponse`:

```python
from src.lib.enum import ReadingStatusEnum

class PaperResponse(BaseModel):
    # ... existing fields ...
    reading_status: str = ReadingStatusEnum.UNREAD.value
```

Add a new update schema:

```python
class PaperStatusUpdate(BaseModel):
    reading_status: ReadingStatusEnum
```

---

### Step 4 — Add Controller Function

**Update file**: `src/controller/papers_controller.py`

Add one new function:

```python
async def update_reading_status(
    paper_id: int, user_id: int, status: ReadingStatusEnum, db: AsyncSession
) -> Paper:
    """
    UPDATE paper SET reading_status = :status
    WHERE id = :paper_id AND user_id = :user_id
    Raise NotFoundError if not found.
    Return updated Paper.
    """
```

Also update `get_all_papers_for_user` to accept an optional status filter:

```python
async def get_all_papers_for_user(
    user_id: int,
    db: AsyncSession,
    status: ReadingStatusEnum | None = None,   # NEW optional filter
) -> list[Paper]:
    """
    SELECT * FROM paper WHERE user_id = :user_id
    AND (:status IS NULL OR reading_status = :status)
    ORDER BY created_at DESC
    """
```

---

### Step 5 — Update the Papers Router

**Update file**: `src/router/papers.py`

Add a query parameter to the existing `GET /` endpoint:

```python
from src.lib.enum import ReadingStatusEnum

@router.get("/", response_model=list[PaperResponse])
async def get_papers(
    status: ReadingStatusEnum | None = Query(default=None),
    user_id: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_all_papers_for_user(user_id, db, status=status)
```

Add a new PATCH endpoint for status updates:

```python
from src.schema.paper import PaperStatusUpdate

@router.patch("/{paper_id}/status", response_model=PaperResponse)
async def update_paper_status(
    paper_id: int,
    payload: PaperStatusUpdate,
    user_id: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the reading status of a specific paper."""
    return await update_reading_status(paper_id, user_id, payload.reading_status, db)
```

---

### Step 6 — Migration

```bash
alembic revision --autogenerate -m "add reading_status to paper"
alembic upgrade head
```

Alembic will generate an `ALTER TABLE paper ADD COLUMN reading_status VARCHAR(20) NOT NULL DEFAULT 'UNREAD'` migration. All existing rows will default to `UNREAD`.

---

---

## 9. Keyword Extraction

### Overview

When a paper is saved, automatically extract the most representative keyphrases from its title and abstract using **KeyBERT** backed by a **SciBERT INT8 ONNX** model (`allenai/scibert_scivocab_uncased`, quantized to INT8). SciBERT was pre-trained on 1.14 million scientific papers from Semantic Scholar — it understands the vocabulary of ArXiv papers far better than a general-purpose BERT model.

The ONNX model runs fully locally via **ONNX Runtime** — no HuggingFace model weight download (~440 MB) required. Only the SciBERT tokenizer config/vocab (~1 MB) is fetched once and cached. The pre-quantized INT8 ONNX file (~110 MB) is stored in `resources/keyword_extract_model/` and loaded directly from disk.

Extracted keywords are:
- Stored in a new `Paper.keywords` column (comma-separated string) so any part of the app can read them without re-running inference.
- Used by the **Smart Alerts engine** to build richer, more precise ArXiv search queries instead of relying on raw category codes like `cs.AI`.
- Optionally surfaced in the paper detail UI as a tag list.

The extraction runs as a **FastAPI `BackgroundTask`** on every paper save — the user never waits for it. SciBERT INT8 ONNX on CPU takes ~0.5–2s per paper (full KeyBERT extraction with MMR deduplication), which is completely acceptable for a background job.

---

### Step 1 — Add Dependencies

**Update file**: `requirements.txt`

```
keybert>=0.8.4
onnxruntime>=1.17.0
transformers>=4.36.0
```

- `keybert` — keyword extraction pipeline (MMR, n-gram candidates, diversity).
- `onnxruntime` — runs the pre-quantized SciBERT ONNX model on CPU. INT8 inference uses native AVX-512 VNNI instructions — no GPU required.
- `transformers` — only the `AutoTokenizer` is used to load the SciBERT vocab/config (~1 MB, cached in `~/.cache/huggingface/`). No model weights are downloaded.

`sentence-transformers` is **not** needed. The ONNX model file (`scibert_scivocab_uncased-int8.onnx`) is pre-quantized and stored locally in `resources/keyword_extract_model/` — it is loaded directly from disk by ONNX Runtime.

---

### Step 2 — Add `keywords` Column to the Paper Model

**Update file**: `src/model/paper.py` — add `keywords: Mapped[str | None] = mapped_column(String(1024), nullable=True)` after the existing `paper_summary` field. Stores comma-separated keyphrases.

---

### Step 3 — Create the Keyword Engine

**New file**: `src/core/keyword_engine/extractor.py`

> **Prerequisite**: `resources/keyword_extract_model/scibert_scivocab_uncased-int8.onnx` (~110 MB) must be in place.

Contains:

- `ONNXSentenceEmbedder(BaseEmbedder)` — KeyBERT-compatible embedder. Loads ONNX session with parallel execution + all graph optimizations. Mean-pools token embeddings into sentence vectors. Batch size 32. Same implementation as validated in `utils/onnx_embedder.py`.

- `get_keyword_model()` — module-level singleton, loads `KeyBERT(model=ONNXSentenceEmbedder())` once (~5–7s cold start).

- `extract_keywords(title, abstract, top_n=10)` — concatenates `title + abstract[:1200]`, runs KeyBERT with `ngram_range=(1,3)`, `use_mmr=True`, `diversity=0.6`. Returns plain string list.

- `keywords_to_string(keywords)` — joins to comma-separated format for `Paper.keywords`.

- `keywords_to_arxiv_query(keywords, max_terms=6)` — builds AND-joined quoted query for ArXiv API. Used by Smart Alerts.

---

### Step 4 — Background Task (Already Defined in Feature 1)

The background task `index_paper_background()` is defined in Feature 1, Step 14. It calls `extract_keywords()` → writes to `Paper.keywords` using `session_pool()`. No vector store upsert — catalog is pre-indexed in Qdrant.

---

### Step 5 — Update the Papers Router

**Update file**: `src/router/papers.py` — add `BackgroundTasks` param to `add_paper()`, call `background_tasks.add_task(index_paper_background, paper_id, title, abstract)` after paper creation. No delete hook needed — keywords live in the DB row.

---

### Step 6 — Update the Paper Schema

**Update file**: `src/schema/paper.py` — add `keywords: Optional[str] = None` to `PaperResponse`. No change to `PaperCreate`.

---

### Step 7 — Wire Keywords into the Smart Alerts Engine

**Update file**: `src/core/alert_engine/alert_job.py` — in `run_alert_job_for_user()`, collect keywords from all user's saved papers, deduplicate via `Counter`, build ArXiv query with `keywords_to_arxiv_query()`. Falls back to raw category codes if no keywords available.

---

### Step 8 — Manual Re-extraction Endpoint (Optional)

**Update file**: `src/router/papers.py` — add `POST /{paper_id}/extract-keywords` (synchronous, ~0.5–2s). Calls `extract_keywords()` and `update_paper_keywords()` in controller.

**Update file**: `src/controller/papers_controller.py` — add `update_paper_keywords(paper_id, user_id, keywords)`.

---

### Step 9 — Migration

```bash
alembic revision --autogenerate -m "add keywords to paper"
alembic upgrade head
```

Nullable — existing papers get `NULL` until re-extraction.

---

### Summary of the Full Flow

```
User saves paper  →  POST /api/v1/papers
                        │
                        ├─ 201 Created (response sent immediately)
                        │
                        └─ index_paper_background() starts in thread pool:
                             │
                             └─ SciBERT ONNX INT8 keyword extraction   ~80ms–2s
                                  extract_keywords(title, abstract[:1200])
                                  -> ["attention mechanism", "transformer", ...]
                                  UPDATE paper SET keywords = "..."

                       No vector store write — catalog is pre-indexed in Qdrant.
                       Recommendations query Qdrant at request time (Feature 1, Step 11).

                       Total background time: ~80ms–2s
                       User waits for: 0ms
```

---

---

## Summary — New Files & Changed Files

### New Files

| Path | Purpose |
|---|---|
| `src/lib/qdrant.py` | Native Qdrant client singleton (recs, server-side inference) + `ensure_collections_exist()` |
| `src/model/arxiv_catalog.py` | ArXiv catalog model (PostgreSQL metadata for feed queries) |
| `src/core/catalog_engine/__init__.py` | Package init |
| `src/core/catalog_engine/ingest.py` | OAI-PMH harvest → PostgreSQL + Qdrant server-side embedding |
| `src/core/catalog_engine/update.py` | Daily delta update job |
| `src/core/recommendation_engine/__init__.py` | Package init |
| `src/core/recommendation_engine/recommender.py` | Hybrid recs: k-NN similar, on-topic, by-author + re-ranking |
| `src/core/keyword_engine/__init__.py` | Package init |
| `src/core/keyword_engine/extractor.py` | KeyBERT + SciBERT ONNX INT8 keyword extraction (local, ~80ms) |
| `resources/keyword_extract_model/scibert_scivocab_uncased-int8.onnx` | Pre-quantized SciBERT INT8 ONNX model (~110 MB) |
| `src/core/background_tasks.py` | Background task on paper save (keyword extraction only) |
| `src/controller/catalog_controller.py` | Feed query against PostgreSQL `arxiv_catalog` table |
| `src/controller/recommendation_controller.py` | Hybrid recommendation pipeline (3 signals + re-rank) |
| `src/core/lit_review_engine/__init__.py` | Package init |
| `src/core/lit_review_engine/lit_review.py` | Literature review generation |
| `src/core/analytics_engine/__init__.py` | Package init |
| `src/core/analytics_engine/trends.py` | Trend & gap computation (PostgreSQL aggregations on `arxiv_catalog`) |
| `src/core/alert_engine/__init__.py` | Package init |
| `src/core/alert_engine/alert_job.py` | ArXiv alert background job, keyword-enriched query |
| `src/model/session_paper.py` | Session↔Paper join table |
| `src/model/alert.py` | Alert model |
| `src/model/collection.py` | Collection + join table |
| `src/model/annotation.py` | Annotation model |
| `src/schema/analytics.py` | Analytics response schemas |
| `src/schema/alert.py` | Alert response schemas |
| `src/schema/collection.py` | Collection schemas |
| `src/schema/annotation.py` | Annotation schemas |
| `src/controller/lit_review_controller.py` | Lit review business logic |
| `src/controller/analytics_controller.py` | Analytics business logic |
| `src/controller/alert_controller.py` | Alert CRUD + trigger |
| `src/controller/collection_controller.py` | Collection CRUD |
| `src/controller/annotation_controller.py` | Annotation CRUD + RAG integration |
| `src/router/papers.py` | Add `GET /{paper_id}/recommendations` endpoint (no new router file) |
| `src/router/lit_review.py` | `/api/v1/literature-review` |
| `src/router/analytics.py` | `/api/v1/analytics` |
| `src/router/alerts.py` | `/api/v1/alerts` |
| `src/router/collections.py` | `/api/v1/collections` |
| `src/router/annotations.py` | `/api/v1/annotations` |

### Changed Files

| Path | What Changes |
|---|---|
| `src/model/paper.py` | Add `reading_status`, `keywords` fields; add `annotations` relationship |
| `src/model/user.py` | Add `collections`, `alerts` relationships |
| `src/model/chat_session.py` | Add `papers` many-to-many relationship |
| `src/core/chat_engine/agent_state.py` | Add `paper_ids`, `paper_titles`, `annotation_context` fields |
| `src/core/vectorstore.py` | Replace `PineconeVectorStore` with `QdrantVectorStore` in `VectorStoreFactory` |
| `src/core/chat_engine/agents/retriever.py` | Update Pinecone filter syntax to Qdrant `Filter` with `FieldCondition` |
| `src/core/chat_engine/agents/generate.py` | Append `annotation_context` to document context |
| `src/core/ingest_engine/ingestion.py` | Update Pinecone type hints and filter syntax to Qdrant |
| `src/config/prompts.py` | Add `LIT_REVIEW_SYSTEM_PROMPT` |
| `src/schema/paper.py` | Add `RecommendationItem`, `RecommendationsResponse`, `LitReviewRequest/Response`, `PaperStatusUpdate`; add `reading_status` and `keywords` to `PaperResponse` |
| `src/controller/papers_controller.py` | Add `status` filter to `get_all_papers_for_user`, add `update_reading_status`, add `update_paper_keywords` |
| `src/controller/chat_controller.py` | Fetch annotation context before graph invocation |
| `src/router/papers.py` | Add `BackgroundTasks` + `index_paper_background` (keyword extraction); add `GET /{id}/recommendations`; add `POST /{id}/extract-keywords`; add `status` query param; add `PATCH /{id}/status` |
| `src/router/arxiv.py` | Replace feed body with PostgreSQL `get_feed()`; remove auto thumbnail endpoint |
| `src/router/sessions.py` | Add `POST /multi` endpoint |
| `main.py` | Register 6 new routers; call `ensure_collections_exist()` on startup; add APScheduler with daily catalog update + alert jobs |
| `requirements.txt` | Add `qdrant-client>=1.12.0`, `langchain-qdrant>=0.2.0`, `sickle>=0.7.0`, `keybert>=0.8.4`, `onnxruntime>=1.17.0`, `transformers>=4.36.0`, `apscheduler>=3.10`, `cachetools>=5.3` |
| `.env` | Add `QDRANT_URI`, `QDRANT_API_KEY`, `COHERE_API_KEY` |

### Migrations Required

```bash
# Run in order
alembic revision --autogenerate -m "add arxiv_catalog table"
alembic revision --autogenerate -m "add reading_status and keywords to paper"
alembic revision --autogenerate -m "add session_paper association table"
alembic revision --autogenerate -m "add alert table"
alembic revision --autogenerate -m "add collection and collection_paper tables"
alembic revision --autogenerate -m "add annotation table"
alembic upgrade head
```

> **Tip**: You can batch all model changes and run a single `--autogenerate` to pick them all up in one migration file. Vectors live in Qdrant Cloud; PostgreSQL stores metadata (`arxiv_catalog`) and user data.

> **Initial catalog load**: After migrations, run the one-time harvest as a management command:
> ```bash
> python -c "
> import asyncio
> from src.database.db import get_db_session
> from src.core.catalog_engine.ingest import load_catalog_from_oai, upsert_catalog_to_qdrant
> async def main():
>     async with get_db_session() as db:
>         n = await load_catalog_from_oai(db, set_spec='cs', from_date='2021-01-01')
>         print(f'Loaded {n} records to PostgreSQL')
>         q = await upsert_catalog_to_qdrant(db)
>         print(f'Indexed {q} rows in Qdrant (server-side embedding)')
> asyncio.run(main())
> "
> ```

---

## Implementation Order (Recommended)

Build in this order to keep each step independently testable:

1. **Reading Status** — Pure model + schema + one endpoint. Zero external dependencies. Validates the Alembic migration pattern used throughout.
2. **Collections** — Self-contained CRUD. Tests the join-table pattern reused in multi-paper chat.
3. **Annotations** — Adds the RAG injection hook. Validates the `AgentState` extension approach.
4. **ArXiv Catalog + Hybrid Recommendations** — Add `lib/qdrant.py` (native client), update `core/vectorstore.py` (Pinecone → Qdrant), set up collections, run OAI-PMH initial load (PostgreSQL + Qdrant server-side embedding), swap the feed endpoint, wire the 3 recommendation signals + re-ranking. This is the largest step — do it before anything that depends on catalog data.
5. **Multi-Paper Chat** — Extends `AgentState` and the retriever. Tests Qdrant `MatchAny` filter on `paper_id`.
6. **Keyword Extraction** — SciBERT ONNX INT8 model loads as part of `index_paper_background()` already wired in step 4. Ensure `resources/keyword_extract_model/scibert_scivocab_uncased-int8.onnx` is in place. Verify keyword quality on a few real saved papers. Wire `keywords_to_arxiv_query()` for use in Alerts.
7. **Smart Alerts** — Uses keywords from step 6 for richer queries against the ArXiv API. Introduce APScheduler alongside the existing catalog update job. Keep as on-demand endpoint first; add cron after verifying query output.
8. **Literature Review** — Reuses `SummaryEngine`. Straightforward once ingestion works.
9. **Trend & Gap Analysis** — Leverage PostgreSQL aggregations on `arxiv_catalog` for trend computation. Add last; needs real accumulated data to be meaningful.
