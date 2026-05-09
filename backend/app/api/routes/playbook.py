import copy
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm.attributes import flag_modified

from app.api.cache import (
    cache_delete_pattern,
    cache_get,
    cache_set,
    checklist_cache_key,
    playbook_cache_key,
    textbook_cache_key,
)
from app.api.deps import get_org_id
from app.database import SessionLocal
from app.models.document import Document
from app.models.organization import Organization
from app.models.playbook import OrgPlaybook, PlaybookEdit
from app.schemas.playbook import (
    ExportRequest,
    OrgPlaybookResponse,
    PlaybookSectionSchema,
    StandardPosition,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/playbook", tags=["playbook"])

_REDIS_TTL = 86400


def _redis():
    import redis

    from app.config import settings

    return redis.from_url(settings.REDIS_URL, decode_responses=True)


def _current_playbook(db, org_id: str):
    return (
        db.query(OrgPlaybook)
        .filter(
            OrgPlaybook.org_id == uuid.UUID(org_id),
            OrgPlaybook.is_current.is_(True),
        )
        .first()
    )


@router.get("/current", response_model=OrgPlaybookResponse)
async def get_current_playbook(request: Request):
    # TODO: replace get_org_id with real auth when auth is implemented
    org_id = get_org_id(request)

    cached = cache_get(playbook_cache_key(org_id))
    if cached:
        return cached

    db = SessionLocal()
    try:
        playbook = _current_playbook(db, org_id)
        if not playbook:
            raise HTTPException(
                status_code=404,
                detail="No playbook generated yet. Upload documents and trigger regeneration.",
            )
        result = _to_response(playbook)
        cache_set(playbook_cache_key(org_id), result.model_dump())
        return result
    finally:
        db.close()


@router.get("/versions")
async def list_playbook_versions(request: Request):
    # TODO: replace get_org_id with real auth when auth is implemented
    org_id = get_org_id(request)
    db = SessionLocal()
    try:
        versions = (
            db.query(OrgPlaybook)
            .filter(OrgPlaybook.org_id == uuid.UUID(org_id))
            .order_by(OrgPlaybook.version.desc())
            .all()
        )
        return [
            {
                "id": str(p.id),
                "version": p.version,
                "generated_at": p.generated_at.isoformat(),
                "doc_count": p.doc_count,
                "is_current": p.is_current,
                "onboarding_ready": p.onboarding_ready,
            }
            for p in versions
        ]
    finally:
        db.close()


@router.post("/regenerate")
async def regenerate_playbook(request: Request):
    # TODO: replace get_org_id with real auth when auth is implemented
    # NOTE: This is the ONLY way to trigger playbook regeneration. Never automatic.
    org_id = get_org_id(request)
    db = SessionLocal()
    try:
        # Require at least one complete document before regenerating
        complete_doc = (
            db.query(Document)
            .filter(
                Document.org_id == uuid.UUID(org_id),
                Document.status == "complete",
                Document.is_deleted.is_(False),
            )
            .first()
        )
        if not complete_doc:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No processed documents found. "
                    "Upload and process documents first."
                ),
            )
    finally:
        db.close()

    from app.tasks.regenerate_playbook import regenerate_playbook as regen_task

    task = regen_task.delay(org_id)

    r = _redis()
    r.setex(
        f"playbook_regen:{org_id}",
        _REDIS_TTL,
        json.dumps(
            {
                "stage": "queued",
                "job_id": task.id,
                "started_at": datetime.now(timezone.utc).isoformat(),
            }
        ),
    )

    return {"message": "Playbook regeneration started", "job_id": task.id}


@router.get("/regenerate/status")
async def get_regenerate_status(request: Request):
    # TODO: replace get_org_id with real auth when auth is implemented
    org_id = get_org_id(request)
    r = _redis()
    raw = r.get(f"playbook_regen:{org_id}")
    if not raw:
        return {"stage": "idle", "started_at": None, "completed_at": None}
    return json.loads(raw)


@router.post("/export")
async def export_playbook(request: Request, body: ExportRequest):
    # TODO: replace get_org_id with real auth when auth is implemented
    org_id = get_org_id(request)

    if body.format not in ("docx", "pdf"):
        raise HTTPException(status_code=400, detail="format must be 'docx' or 'pdf'")

    db = SessionLocal()
    try:
        playbook = _current_playbook(db, org_id)
        if not playbook:
            raise HTTPException(status_code=404, detail="No playbook found.")

        org = db.query(Organization).filter(Organization.id == uuid.UUID(org_id)).first()
        org_name = org.name if org else "Your Organization"

        out_dir = Path(f"/tmp/lexonboard/exports/{org_id}")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"playbook_v{playbook.version}.{body.format}"

        if body.format == "docx":
            from app.services.export.word_exporter import export_playbook_to_docx

            data = export_playbook_to_docx(playbook, org_name=org_name)
            media_type = (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        else:
            from app.services.export.pdf_exporter import export_playbook_to_pdf

            data = export_playbook_to_pdf(playbook, org_name=org_name)
            media_type = "application/pdf"

        out_path.write_bytes(data)

        return FileResponse(
            path=str(out_path),
            media_type=media_type,
            filename=out_path.name,
        )
    finally:
        db.close()


@router.patch("/sections/{clause_type}")
async def update_playbook_section(clause_type: str, request: Request):
    # TODO: replace get_org_id with real auth when auth is implemented
    org_id = get_org_id(request)
    body = await request.json()

    db = SessionLocal()
    try:
        playbook = _current_playbook(db, org_id)
        if not playbook:
            raise HTTPException(status_code=404, detail="No current playbook found.")

        sections = copy.deepcopy(playbook.sections or [])
        target_idx = next(
            (i for i, s in enumerate(sections) if s.get("clause_type") == clause_type),
            None,
        )
        if target_idx is None:
            raise HTTPException(
                status_code=404,
                detail=f"Section '{clause_type}' not found in current playbook.",
            )

        # Merge edit into section (not replace)
        sections[target_idx] = {**sections[target_idx], **body}
        playbook.sections = sections
        flag_modified(playbook, "sections")

        # Audit record
        user_id_str = request.headers.get("X-User-ID", "dev-user-001")
        try:
            editor_uuid = uuid.UUID(user_id_str)
        except ValueError:
            editor_uuid = None

        edit = PlaybookEdit(
            id=uuid.uuid4(),
            playbook_id=playbook.id,
            clause_type=clause_type,
            edited_by=editor_uuid,
            edit_data=body,
            approved=False,
        )
        db.add(edit)
        db.commit()

        return sections[target_idx]
    finally:
        db.close()


def _to_response(playbook: OrgPlaybook) -> OrgPlaybookResponse:
    sections = [
        PlaybookSectionSchema(
            clause_type=s.get("clause_type", ""),
            title=s.get("title", ""),
            non_negotiables=s.get("non_negotiables", []),
            standard_positions=[
                StandardPosition(**p) for p in s.get("standard_positions", [])
            ],
            red_flags=s.get("red_flags", []),
            industry_baseline=s.get("industry_baseline", ""),
            example_clauses=s.get("example_clauses", []),
            source_doc_ids=s.get("source_doc_ids", []),
        )
        for s in (playbook.sections or [])
    ]
    return OrgPlaybookResponse(
        id=str(playbook.id),
        version=playbook.version,
        generated_at=playbook.generated_at,
        is_current=playbook.is_current,
        sections=sections,
        onboarding_ready=playbook.onboarding_ready,
        doc_count=playbook.doc_count,
    )
