import logging
import uuid

from app.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "contract_clauses"
VECTOR_SIZE = 384  # BAAI/bge-small-en-v1.5 output dimension


class EmbeddingService:
    _model = None
    _qdrant = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            from sentence_transformers import SentenceTransformer

            logger.info("Loading BAAI/bge-small-en-v1.5 embedding model (first use)")
            cls._model = SentenceTransformer("BAAI/bge-small-en-v1.5")
            logger.info("Embedding model loaded.")
        return cls._model

    @classmethod
    def get_qdrant(cls):
        if cls._qdrant is None:
            from qdrant_client import QdrantClient

            cls._qdrant = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
            )
        return cls._qdrant

    @classmethod
    def ensure_collection_exists(cls) -> None:
        from qdrant_client.models import Distance, VectorParams

        client = cls.get_qdrant()
        existing = {c.name for c in client.get_collections().collections}

        if COLLECTION_NAME not in existing:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
            logger.info(f"Created Qdrant collection '{COLLECTION_NAME}'")

    @classmethod
    def embed_and_upsert(cls, processed_clauses: list[dict], org_id: str) -> dict:
        """
        Embed clauses and upsert vectors to Qdrant.
        processed_clauses must have keys: id, raw_text, clause_type, document_id.
        Returns {clause_db_id: qdrant_point_id}.
        """
        if not processed_clauses:
            return {}

        from qdrant_client.models import PointStruct

        cls.ensure_collection_exists()
        model = cls.get_model()
        client = cls.get_qdrant()

        texts = [c["raw_text"] for c in processed_clauses]
        embeddings = model.encode(texts, batch_size=32, show_progress_bar=False)

        id_map: dict[str, str] = {}
        points: list[PointStruct] = []

        for embedding, clause in zip(embeddings, processed_clauses):
            point_id = str(uuid.uuid4())
            id_map[clause["id"]] = point_id

            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload={
                        "org_id": org_id,
                        "clause_type": clause["clause_type"],
                        "document_id": clause["document_id"],
                        "clause_db_id": clause["id"],
                    },
                )
            )

        # Upsert in batches of 100
        for i in range(0, len(points), 100):
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=points[i : i + 100],
            )

        logger.info(f"Upserted {len(points)} clause embeddings to Qdrant for org {org_id}")
        return id_map