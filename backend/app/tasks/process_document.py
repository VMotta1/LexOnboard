import json
import logging
import uuid
from datetime import datetime, timezone

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.clause import ProcessedClause, RawClause
from app.models.document import Document

logger = logging.getLogger(__name__)

_REDIS_JOB_TTL = 86400  # 24 hours


def _redis():
    import redis

    from app.config import settings

    return redis.from_url(settings.REDIS_URL, decode_responses=True)


def _set_job_state(
    task_id: str,
    stage: str,
    progress_pct: int,
    document_id: str,
    org_id: str,
    error: str | None = None,
) -> None:
    r = _redis()
    state = {
        "stage": stage,
        "progress_pct": progress_pct,
        "document_id": document_id,
        "org_id": org_id,
        "error": error,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    r.setex(f"job:{task_id}", _REDIS_JOB_TTL, json.dumps(state))


def _update_doc_status(
    db, document_id: str, status: str, error: str | None = None
) -> None:
    doc = db.query(Document).filter(Document.id == document_id).first()
    if doc:
        doc.status = status
        if error is not None:
            doc.error_message = error
        db.commit()


def _process_document_impl(document_id: str, task_id: str) -> None:
    """
    Core document-processing pipeline. Callable from either a Celery task or a
    FastAPI BackgroundTasks coroutine. The task_id is used to key the Redis job
    state the frontend polls.

    Stages: ingesting (10→30) → nlp_processing (35→80) → complete (100).
    """
    db = SessionLocal()
    org_id = ""

    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Document {document_id} not found in DB")
            return

        org_id = str(doc.org_id)
        file_path = doc.storage_path
        doc_type = doc.doc_type
        is_ocr = bool((doc.metadata_ or {}).get("likely_ocr", False))

        if is_ocr:
            logger.warning(
                f"⚠ OCR mode — processing may take 2-5 min for doc {document_id}"
            )

        _set_job_state(task_id, "ingesting", 10, document_id, org_id)
        _update_doc_status(db, document_id, "ingesting")

        from app.services.ingestion.extractor import extract_and_chunk

        raw_chunks = extract_and_chunk(file_path, doc_type)
        logger.info(
            f"{len(raw_chunks)} clause chunks extracted "
            f"{'(OCR) ' if is_ocr else ''}from {document_id}"
        )

        raw_records: list[RawClause] = []
        for chunk in raw_chunks:
            rc = RawClause(
                id=uuid.uuid4(),
                document_id=uuid.UUID(document_id),
                org_id=uuid.UUID(org_id),
                text=chunk["text"],
                section_path=chunk.get("section_path", []),
                page_number=chunk.get("page_number", 0),
                char_offset=chunk.get("char_offset", 0),
            )
            db.add(rc)
            raw_records.append(rc)

        db.commit()
        _set_job_state(task_id, "ingesting", 30, document_id, org_id)

        _set_job_state(task_id, "nlp", 35, document_id, org_id)
        _update_doc_status(db, document_id, "nlp_processing")

        from app.services.nlp.pipeline import process_document_nlp

        raw_dicts = [
            {"id": str(rc.id), "text": rc.text, "section_path": rc.section_path}
            for rc in raw_records
        ]
        processed_dicts = process_document_nlp(raw_dicts, org_id, document_id)

        raw_by_id = {str(rc.id): rc for rc in raw_records}

        processed_records: list[ProcessedClause] = []
        for pd in processed_dicts:
            raw_rec = raw_by_id.get(pd["raw_clause_id"])
            if raw_rec is None:
                continue

            pc = ProcessedClause(
                id=uuid.UUID(pd["id"]),
                raw_clause_id=raw_rec.id,
                org_id=uuid.UUID(org_id),
                clause_type=pd["clause_type"],
                clause_type_confidence=pd["clause_type_confidence"],
                entities=pd["entities"],
                obligations=pd["obligations"],
                raw_text=pd["raw_text"],
                embedding_id=None,
            )
            db.add(pc)
            processed_records.append(pc)

        db.commit()
        _set_job_state(task_id, "nlp", 65, document_id, org_id)

        from app.services.retrieval.embedder import EmbeddingService

        embed_input = [
            {
                "id": str(pc.id),
                "raw_text": pc.raw_text,
                "clause_type": pc.clause_type,
                "document_id": document_id,
            }
            for pc in processed_records
        ]
        id_map = EmbeddingService.embed_and_upsert(embed_input, org_id)

        for pc in processed_records:
            qdrant_id = id_map.get(str(pc.id))
            if qdrant_id:
                pc.embedding_id = qdrant_id

        db.commit()
        _set_job_state(task_id, "nlp", 80, document_id, org_id)

        _update_doc_status(db, document_id, "complete")
        _set_job_state(task_id, "complete", 100, document_id, org_id)

        logger.info(
            f"✓ Document {document_id} processed. "
            f"{len(processed_records)} clauses indexed. "
            "Admin must manually trigger playbook regeneration."
        )

    except Exception as exc:
        logger.error(
            f"_process_document_impl failed for {document_id}: {exc}",
            exc_info=True,
        )
        try:
            _update_doc_status(db, document_id, "error", str(exc))
            _set_job_state(task_id, "error", 0, document_id, org_id, str(exc))
        except Exception:
            pass
        raise

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_document(self, document_id: str):
    """Celery wrapper around `_process_document_impl`."""
    try:
        _process_document_impl(document_id, self.request.id)
    except Exception as exc:
        raise self.retry(exc=exc)