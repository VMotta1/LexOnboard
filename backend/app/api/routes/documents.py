import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, UploadFile
from fastapi.params import File, Form

from app.api.deps import get_org_id
from app.database import SessionLocal
from app.models.document import Document
from app.schemas.document import DocumentListItem, DocumentUploadResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
_ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
_ALLOWED_EXTENSIONS = {".pdf", ".docx"}
_REDIS_JOB_TTL = 86400  # 24 hours


def _redis():
    import redis

    from app.config import settings

    return redis.from_url(settings.REDIS_URL, decode_responses=True)


def _detect_likely_ocr(file_path: str) -> bool:
    """Quick check: is the PDF image-based (scanned)?"""
    if not file_path.lower().endswith(".pdf"):
        return False
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(file_path)
        total_text = "".join(doc[i].get_text() for i in range(min(3, len(doc))))
        doc.close()
        return len(total_text.strip()) < 100
    except Exception:
        return False


def _inline_processing_enabled() -> bool:
    return os.getenv("LEXONBOARD_INLINE_PROCESSING", "true").lower() in {
        "1",
        "true",
        "yes",
    }


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    doc_type: str = Form(...),
):
    # TODO: replace get_org_id with real auth when auth is implemented
    org_id = get_org_id(request)

    # Validate file extension
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Only PDF and DOCX are accepted.",
        )

    # Normalize doc_type (accept display names or slugs from frontend)
    _DOC_TYPE_MAP = {
        "master agreement": "master_agreement",
        "master_agreement": "master_agreement",
        "compliance document": "compliance",
        "compliance": "compliance",
        "nda": "nda",
        "statement of work": "sow",
        "sow": "sow",
        "other": "other",
    }
    doc_type = _DOC_TYPE_MAP.get(doc_type.lower(), "")
    if not doc_type:
        raise HTTPException(
            status_code=400,
            detail="Invalid doc_type. Accepted: Master Agreement, Compliance Document, NDA, Statement of Work, Other",
        )

    # Read content and enforce size limit
    content = await file.read()
    if len(content) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds 50 MB limit ({len(content) / 1_048_576:.1f} MB).",
        )

    doc_id = uuid.uuid4()

    # Persist to local /tmp/lexonboard/{org_id}/{doc_id}/{filename}
    save_dir = Path(f"/tmp/lexonboard/{org_id}/{doc_id}")
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / (file.filename or f"{doc_id}{suffix}")

    with open(save_path, "wb") as f_out:
        f_out.write(content)

    # OCR detection after saving (quick PyMuPDF check)
    likely_ocr = _detect_likely_ocr(str(save_path))

    db = SessionLocal()
    try:
        doc = Document(
            id=doc_id,
            org_id=uuid.UUID(org_id),
            filename=file.filename or str(doc_id),
            doc_type=doc_type,
            storage_path=str(save_path),
            status="pending",
            metadata_={"likely_ocr": likely_ocr},
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        from app.config import settings as _settings
        if _settings.DEMO_MODE:
            # In demo mode: skip real Celery pipeline, mark document complete immediately
            mock_job_id = f"demo-{doc_id}"
            doc.status = "complete"
            doc.job_id = mock_job_id
            db.commit()
            r = _redis()
            r.setex(
                f"job:{mock_job_id}",
                _REDIS_JOB_TTL,
                json.dumps({
                    "stage": "complete",
                    "progress_pct": 100,
                    "document_id": str(doc_id),
                    "org_id": org_id,
                    "error": None,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }),
            )
        elif _inline_processing_enabled():
            # macOS dev fallback: run pipeline in-process via FastAPI BackgroundTasks
            # to bypass Celery's libomp/SHM2 incompatibility with PyTorch on arm64.
            from app.tasks.process_document import _process_document_impl

            task_id = str(uuid.uuid4())
            r = _redis()
            r.setex(
                f"job:{task_id}",
                _REDIS_JOB_TTL,
                json.dumps(
                    {
                        "stage": "queued",
                        "progress_pct": 0,
                        "document_id": str(doc_id),
                        "org_id": org_id,
                        "error": None,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                ),
            )

            doc.job_id = task_id
            db.commit()

            background_tasks.add_task(
                _process_document_impl, str(doc_id), task_id
            )
        else:
            from app.tasks.process_document import process_document
            task = process_document.delay(str(doc_id))

            # Store initial job state in Redis
            r = _redis()
            state = {
                "stage": "queued",
                "progress_pct": 0,
                "document_id": str(doc_id),
                "org_id": org_id,
                "error": None,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            r.setex(f"job:{task.id}", _REDIS_JOB_TTL, json.dumps(state))

            # Persist task id back onto Document
            doc.job_id = task.id
            db.commit()

        return DocumentUploadResponse(
            id=str(doc.id),
            filename=doc.filename,
            doc_type=doc.doc_type,
            status=doc.status,
            job_id=doc.job_id,
        )
    finally:
        db.close()


@router.get("/", response_model=list[DocumentListItem])
async def list_documents(request: Request):
    # TODO: replace get_org_id with real auth when auth is implemented
    org_id = get_org_id(request)

    db = SessionLocal()
    try:
        docs = (
            db.query(Document)
            .filter(
                Document.org_id == uuid.UUID(org_id),
                Document.is_deleted.is_(False),
            )
            .order_by(Document.upload_date.desc())
            .all()
        )
        return [
            DocumentListItem(
                id=str(d.id),
                filename=d.filename,
                doc_type=d.doc_type,
                status=d.status,
                upload_date=d.upload_date,
                page_count=d.page_count,
            )
            for d in docs
        ]
    finally:
        db.close()


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, request: Request):
    # TODO: replace get_org_id with real auth when auth is implemented
    org_id = get_org_id(request)

    db = SessionLocal()
    try:
        doc = (
            db.query(Document)
            .filter(
                Document.id == uuid.UUID(doc_id),
                Document.org_id == uuid.UUID(org_id),
                Document.is_deleted.is_(False),
            )
            .first()
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")

        doc.is_deleted = True
        db.commit()

        # Playbook regeneration is NOT triggered automatically.
        return {
            "message": "deleted",
            "note": (
                "Regenerate the playbook from the Playbook page to reflect this removal."
            ),
        }
    finally:
        db.close()


@router.get("/{doc_id}/retry")
async def retry_document(doc_id: str, request: Request):
    # TODO: replace get_org_id with real auth when auth is implemented
    org_id = get_org_id(request)

    db = SessionLocal()
    try:
        doc = (
            db.query(Document)
            .filter(
                Document.id == uuid.UUID(doc_id),
                Document.org_id == uuid.UUID(org_id),
                Document.is_deleted.is_(False),
            )
            .first()
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")

        if doc.status != "error":
            raise HTTPException(
                status_code=400,
                detail=f"Document is not in error state (current: {doc.status}).",
            )

        doc.status = "pending"
        doc.error_message = None
        db.commit()

        from app.tasks.process_document import process_document

        task = process_document.delay(str(doc_id))

        r = _redis()
        state = {
            "stage": "queued",
            "progress_pct": 0,
            "document_id": doc_id,
            "org_id": org_id,
            "error": None,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        r.setex(f"job:{task.id}", _REDIS_JOB_TTL, json.dumps(state))

        doc.job_id = task.id
        db.commit()

        return {"message": "requeued", "job_id": task.id}
    finally:
        db.close()