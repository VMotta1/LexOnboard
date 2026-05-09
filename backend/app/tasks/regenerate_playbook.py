import json
import logging
import uuid
from datetime import datetime, timezone

from app.api.cache import cache_delete_pattern, playbook_cache_key, textbook_cache_key, checklist_cache_key
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.clause import ProcessedClause
from app.models.playbook import OrgPlaybook

logger = logging.getLogger(__name__)

_REDIS_TTL = 86400  # 24 hours


def _redis():
    import redis

    from app.config import settings

    return redis.from_url(settings.REDIS_URL, decode_responses=True)


def _set_regen_state(org_id: str, stage: str, job_id: str = "") -> None:
    r = _redis()
    state = {
        "stage": stage,
        "job_id": job_id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    r.setex(f"playbook_regen:{org_id}", _REDIS_TTL, json.dumps(state))


@celery_app.task
def regenerate_playbook(org_id: str):
    """
    Admin-triggered task: distil all ProcessedClauses → OrgPlaybook.
    Never called automatically — only via POST /api/playbook/regenerate.
    """
    db = SessionLocal()
    try:
        _set_regen_state(org_id, "running")

        # Load all processed clauses for this org
        all_clauses = (
            db.query(ProcessedClause)
            .filter(ProcessedClause.org_id == uuid.UUID(org_id))
            .all()
        )

        if not all_clauses:
            logger.warning(f"regenerate_playbook: no ProcessedClauses found for org {org_id}")
            _set_regen_state(org_id, "error")
            return

        # Group by clause_type
        by_type: dict[str, list] = {}
        for clause in all_clauses:
            by_type.setdefault(clause.clause_type, []).append(clause)

        # Synthesize each clause type that has >= 2 examples
        from app.services.distillation.synthesizer import synthesize_clause_type

        sections = []
        for clause_type, clauses in by_type.items():
            if len(clauses) < 2:
                logger.debug(
                    f"Skipping '{clause_type}' — only {len(clauses)} clause(s), need >= 2"
                )
                continue
            section = synthesize_clause_type(clause_type, clauses)
            if section is not None:
                sections.append(section)

        if not sections:
            logger.warning(
                f"regenerate_playbook: no sections generated for org {org_id} — "
                "ensure documents have >= 2 clauses of the same type"
            )
            _set_regen_state(org_id, "error")
            return

        # Determine next version
        current = (
            db.query(OrgPlaybook)
            .filter(
                OrgPlaybook.org_id == uuid.UUID(org_id),
                OrgPlaybook.is_current.is_(True),
            )
            .first()
        )
        next_version = (current.version + 1) if current else 1
        doc_count = len({c.raw_clause_id for c in all_clauses})  # unique raw clauses

        # Retire the current playbook
        if current:
            current.is_current = False
            db.commit()

        # Merge and persist the new playbook
        from app.services.distillation.merger import merge_into_playbook

        playbook_data = merge_into_playbook(
            org_id=org_id,
            sections=sections,
            doc_count=doc_count,
            next_version=next_version,
        )

        new_playbook = OrgPlaybook(
            id=uuid.uuid4(),
            org_id=uuid.UUID(org_id),
            version=playbook_data["version"],
            is_current=True,
            sections=playbook_data["sections"],
            doc_count=playbook_data["doc_count"],
            onboarding_ready=False,
        )
        db.add(new_playbook)
        db.commit()
        db.refresh(new_playbook)

        logger.info(
            f"Playbook v{new_playbook.version} generated with {len(sections)} sections "
            f"from {doc_count} clauses for org {org_id}"
        )

        # Invalidate response caches for this org
        cache_delete_pattern(playbook_cache_key(org_id))
        cache_delete_pattern(textbook_cache_key(org_id))
        cache_delete_pattern(checklist_cache_key(org_id))

        # Enqueue onboarding generation
        from app.tasks.generate_onboarding import generate_onboarding

        generate_onboarding.delay(org_id, str(new_playbook.id))

        _set_regen_state(org_id, "complete", job_id=str(new_playbook.id))

    except Exception as exc:
        logger.error(f"regenerate_playbook failed for org {org_id}: {exc}", exc_info=True)
        _set_regen_state(org_id, "error")
        raise
    finally:
        db.close()
