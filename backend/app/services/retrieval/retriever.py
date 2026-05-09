import logging
import uuid

from app.database import SessionLocal
from app.models.clause import ProcessedClause, RawClause
from app.services.retrieval.embedder import COLLECTION_NAME, EmbeddingService

logger = logging.getLogger(__name__)


def retrieve_relevant_clauses(
    question: str,
    org_id: str,
    top_k: int = 5,
) -> list[dict]:
    """
    Embed question → search Qdrant (org-scoped) → load full clause text from PostgreSQL.
    Returns list[{id, clause_type, section_path, raw_text, score}] sorted by score desc.
    """
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    # Embed question using same model as the indexed clauses
    model = EmbeddingService.get_model()
    embedding = model.encode([question], show_progress_bar=False)[0].tolist()

    client = EmbeddingService.get_qdrant()
    hits = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=embedding,
        limit=top_k,
        with_payload=True,
        query_filter=Filter(
            must=[
                FieldCondition(key="org_id", match=MatchValue(value=org_id))
            ]
        ),
    )

    if not hits:
        return []

    db = SessionLocal()
    try:
        results: list[dict] = []
        for hit in hits:
            payload = hit.payload or {}
            clause_db_id = payload.get("clause_db_id")
            if not clause_db_id:
                continue

            try:
                pc_id = uuid.UUID(clause_db_id)
            except (ValueError, TypeError):
                continue

            # Join ProcessedClause + RawClause to get section_path
            row = (
                db.query(ProcessedClause, RawClause)
                .join(RawClause, ProcessedClause.raw_clause_id == RawClause.id)
                .filter(ProcessedClause.id == pc_id)
                .first()
            )
            if row is None:
                continue

            pc, raw = row
            results.append(
                {
                    "id": str(pc.id),
                    "clause_type": pc.clause_type,
                    "section_path": raw.section_path or [],
                    "raw_text": pc.raw_text,
                    "score": hit.score,
                }
            )

        results.sort(key=lambda r: r["score"], reverse=True)
        return results

    finally:
        db.close()
