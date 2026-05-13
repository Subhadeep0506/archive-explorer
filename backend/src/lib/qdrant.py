import os
from qdrant_client import QdrantClient, models
from ..core.logger import SingletonLogger

logger = SingletonLogger().get_logger()

CATALOG_COLLECTION = "arxiv-papers"
CHUNKS_COLLECTION = "paper-chunks"
CATALOG_EMBED_MODEL = "intfloat/multilingual-e5-small"
CHUNKS_EMBED_DIM = 1024

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
    """Create arxiv-papers (recs) and paper-chunks (RAG) collections if missing."""
    client = get_qdrant_client()

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
        client.create_payload_index(
            collection_name=CATALOG_COLLECTION,
            field_name="primary_category",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        logger.info(f"Collection {CATALOG_COLLECTION} created with indexes")

    if not client.collection_exists(CHUNKS_COLLECTION):
        logger.info(f"Creating Qdrant collection: {CHUNKS_COLLECTION}")
        client.create_collection(
            collection_name=CHUNKS_COLLECTION,
            vectors_config=models.VectorParams(
                size=CHUNKS_EMBED_DIM,
                distance=models.Distance.COSINE,
            ),
        )
        client.create_payload_index(
            collection_name=CHUNKS_COLLECTION,
            field_name="metadata.paper_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        logger.info(f"Collection {CHUNKS_COLLECTION} created with indexes")
