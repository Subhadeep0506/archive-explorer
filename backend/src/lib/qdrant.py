import os
import time
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import ResponseHandlingException
from ..core.logger import SingletonLogger

logger = SingletonLogger().get_logger()

CATALOG_COLLECTION = "arxiv-papers"
CHUNKS_COLLECTION = "paper-chunks"
CATALOG_EMBED_MODEL = "intfloat/multilingual-e5-small"
CHUNKS_EMBED_DIM = 1024

_client: QdrantClient | None = None


def _create_client() -> QdrantClient:
    return QdrantClient(
        url=os.environ["QDRANT_URI"],
        port=int(os.environ.get("QDRANT_PORT", "443")),
        api_key=os.environ["QDRANT_API_KEY"],
        cloud_inference=True,
        check_compatibility=False,
    )


def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = _create_client()
    return _client


def reset_qdrant_client() -> QdrantClient:
    """Discard the stale client and create a fresh one."""
    global _client
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
    _client = _create_client()
    logger.info("Qdrant client reset due to stale connection")
    return _client


def _ensure_catalog_indexes(client: QdrantClient) -> None:
    """Ensure all required payload indexes exist on the catalog collection."""
    info = client.get_collection(CATALOG_COLLECTION)
    existing = set(info.payload_schema.keys()) if info.payload_schema else set()

    if "arxiv_id" not in existing:
        logger.info("Creating keyword index on arxiv_id")
        client.create_payload_index(
            collection_name=CATALOG_COLLECTION,
            field_name="arxiv_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

    if "primary_category" not in existing:
        logger.info("Creating keyword index on primary_category")
        client.create_payload_index(
            collection_name=CATALOG_COLLECTION,
            field_name="primary_category",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

    if "authors" not in existing:
        logger.info("Creating text index on authors")
        client.create_payload_index(
            collection_name=CATALOG_COLLECTION,
            field_name="authors",
            field_schema=models.TextIndexParams(
                type=models.TextIndexType.TEXT,
                tokenizer=models.TokenizerType.WORD,
                min_token_len=2,
                max_token_len=20,
            ),
        )


def _ensure_chunks_indexes(client: QdrantClient) -> None:
    """Ensure all required payload indexes exist on the chunks collection."""
    if not client.collection_exists(CHUNKS_COLLECTION):
        return
    info = client.get_collection(CHUNKS_COLLECTION)
    existing = set(info.payload_schema.keys()) if info.payload_schema else set()

    if "metadata.paper_id" not in existing:
        logger.info("Creating keyword index on metadata.paper_id")
        client.create_payload_index(
            collection_name=CHUNKS_COLLECTION,
            field_name="metadata.paper_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )


def ensure_collections_exist() -> None:
    """Create arxiv-papers (recs) and paper-chunks (RAG) collections if missing.

    Retries up to 3 times with backoff to handle stale/reset TCP connections
    (common on Windows when Qdrant Cloud closes idle sockets).
    """
    client = None
    for attempt in range(3):
        try:
            client = get_qdrant_client()
            client.get_collections()
            break
        except (ResponseHandlingException, Exception) as exc:
            delay = (attempt + 1) * 2
            logger.warning(
                f"Qdrant connection attempt {attempt + 1}/3 failed: {exc} — retrying in {delay}s",
            )
            time.sleep(delay)
            client = reset_qdrant_client()
    else:
        logger.error("Could not connect to Qdrant after 3 attempts, skipping collection setup")
        return

    if not client.collection_exists(CATALOG_COLLECTION):
        logger.info(f"Creating Qdrant collection: {CATALOG_COLLECTION}")
        client.create_collection(
            collection_name=CATALOG_COLLECTION,
            vectors_config={
                CATALOG_EMBED_MODEL: models.VectorParams(
                    size=384,
                    distance=models.Distance.COSINE,
                )
            },
            quantization_config=models.ScalarQuantization(
                scalar=models.ScalarQuantizationConfig(
                    type=models.ScalarType.INT8,
                    always_ram=True,
                ),
            ),
        )
        logger.info(f"Collection {CATALOG_COLLECTION} created")

    _ensure_catalog_indexes(client)

    if not client.collection_exists(CHUNKS_COLLECTION):
        logger.info(f"Creating Qdrant collection: {CHUNKS_COLLECTION}")
        client.create_collection(
            collection_name=CHUNKS_COLLECTION,
            vectors_config=models.VectorParams(
                size=CHUNKS_EMBED_DIM,
                distance=models.Distance.COSINE,
            ),
        )
        logger.info(f"Collection {CHUNKS_COLLECTION} created")

    _ensure_chunks_indexes(client)
