import logging
import uuid

from app.services.nlp.classifier import ClauseClassifier
from app.services.nlp.ner import NERService
from app.services.nlp.obligation import extract_obligations

logger = logging.getLogger(__name__)


def process_clause(raw_clause: dict, org_id: str, document_id: str) -> dict:
    """
    Run NER + classification + obligation extraction on one raw clause.
    raw_clause must have keys: id (RawClause DB id), text, section_path.
    """
    raw_text = raw_clause["text"]

    entities = NERService.extract_entities(raw_text)
    clause_type, confidence = ClauseClassifier.classify(raw_text)
    obligations = extract_obligations(raw_text)

    return {
        "id": str(uuid.uuid4()),            # ProcessedClause DB id
        "raw_clause_id": raw_clause["id"],  # RawClause DB id
        "org_id": org_id,
        "document_id": document_id,
        "clause_type": clause_type,
        "clause_type_confidence": confidence,
        "entities": entities,
        "obligations": obligations,
        "raw_text": raw_text,
        "embedding_id": None,
    }


def process_document_nlp(
    raw_clauses: list[dict],
    org_id: str,
    document_id: str,
) -> list[dict]:
    """Run the NLP pipeline over every raw clause for a document."""
    processed: list[dict] = []
    total = len(raw_clauses)

    for i, raw in enumerate(raw_clauses):
        try:
            result = process_clause(raw, org_id, document_id)
            processed.append(result)
        except Exception as exc:
            logger.warning(f"Skipping clause {i + 1}/{total} — NLP error: {exc}")
            continue

        if (i + 1) % 10 == 0:
            logger.info(f"NLP progress: {i + 1}/{total} clauses processed")

    logger.info(
        f"NLP complete: {len(processed)}/{total} clauses processed successfully"
    )
    return processed