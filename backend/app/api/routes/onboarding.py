import logging
import uuid

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy.orm.attributes import flag_modified

from app.api.deps import get_org_id, get_user_context
from app.database import SessionLocal
from app.models.onboarding import (
    ContractChecklist,
    OnboardingProgress,
    QuizSet,
    TextbookContent,
)
from app.models.playbook import OrgPlaybook
from app.schemas.onboarding import (
    ContractChecklistResponse,
    OnboardingProgressResponse,
    OnboardingProgressUpdate,
    QuizSetResponse,
    TextbookResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


def _current_playbook(db, org_id: str):
    return (
        db.query(OrgPlaybook)
        .filter(
            OrgPlaybook.org_id == uuid.UUID(org_id),
            OrgPlaybook.is_current.is_(True),
        )
        .first()
    )


@router.get("/textbook", response_model=TextbookResponse)
async def get_textbook(request: Request):
    # TODO: replace get_org_id with real auth when auth is implemented
    org_id = get_org_id(request)
    db = SessionLocal()
    try:
        playbook = _current_playbook(db, org_id)
        if not playbook:
            raise HTTPException(status_code=404, detail="No playbook found.")

        textbook = (
            db.query(TextbookContent)
            .filter(TextbookContent.playbook_id == playbook.id)
            .order_by(TextbookContent.generated_at.desc())
            .first()
        )
        if not textbook:
            raise HTTPException(
                status_code=404,
                detail="Textbook not generated yet. Regenerate the playbook to trigger generation.",
            )

        return TextbookResponse(
            id=str(textbook.id),
            chapters=textbook.chapters or [],
            page_estimate=textbook.page_estimate,
            generated_at=textbook.generated_at,
        )
    finally:
        db.close()


@router.get("/quizzes", response_model=list[QuizSetResponse])
async def get_quizzes(request: Request):
    # TODO: replace get_org_id with real auth when auth is implemented
    org_id = get_org_id(request)
    db = SessionLocal()
    try:
        playbook = _current_playbook(db, org_id)
        if not playbook:
            raise HTTPException(status_code=404, detail="No playbook found.")

        quiz_sets = (
            db.query(QuizSet)
            .filter(QuizSet.playbook_id == playbook.id)
            .order_by(QuizSet.chapter_index.asc().nulls_last())
            .all()
        )
        return [
            QuizSetResponse(
                id=str(qs.id),
                quiz_type=qs.quiz_type,
                questions=qs.questions or [],
            )
            for qs in quiz_sets
        ]
    finally:
        db.close()


@router.get("/checklist", response_model=ContractChecklistResponse)
async def get_checklist(request: Request):
    # TODO: replace get_org_id with real auth when auth is implemented
    org_id = get_org_id(request)
    db = SessionLocal()
    try:
        playbook = _current_playbook(db, org_id)
        if not playbook:
            raise HTTPException(status_code=404, detail="No playbook found.")

        checklist = (
            db.query(ContractChecklist)
            .filter(ContractChecklist.playbook_id == playbook.id)
            .order_by(ContractChecklist.generated_at.desc())
            .first()
        )
        if not checklist:
            raise HTTPException(
                status_code=404,
                detail="Checklist not generated yet.",
            )
        return ContractChecklistResponse(
            id=str(checklist.id),
            categories=checklist.categories or [],
        )
    finally:
        db.close()


@router.get("/progress", response_model=OnboardingProgressResponse)
async def get_progress(request: Request):
    # TODO: replace get_org_id with real auth when auth is implemented
    ctx = get_user_context(request)
    org_id = ctx["org_id"]
    user_id = ctx["user_id"]

    db = SessionLocal()
    try:
        progress = _get_or_create_progress(db, user_id, org_id)
        return _build_progress_response(db, org_id, progress)
    finally:
        db.close()


@router.patch("/progress", response_model=OnboardingProgressResponse)
async def update_progress(request: Request, body: OnboardingProgressUpdate):
    # TODO: replace get_org_id with real auth when auth is implemented
    ctx = get_user_context(request)
    org_id = ctx["org_id"]
    user_id = ctx["user_id"]

    db = SessionLocal()
    try:
        progress = _get_or_create_progress(db, user_id, org_id)

        # Merge new chapters_read (union)
        if body.chapters_read:
            existing = set(progress.chapters_read or [])
            existing.update(body.chapters_read)
            progress.chapters_read = sorted(existing)
            flag_modified(progress, "chapters_read")

        # Update quiz score
        if body.quiz_score:
            quiz_id = body.quiz_score.quiz_id
            score = body.quiz_score.score

            scores = dict(progress.quiz_scores or {})
            scores[quiz_id] = score
            progress.quiz_scores = scores
            flag_modified(progress, "quiz_scores")

            # Only mark as completed if 100% — mastery threshold
            if score == 1.0:
                completed = list(progress.quizzes_completed or [])
                if quiz_id not in completed:
                    completed.append(quiz_id)
                progress.quizzes_completed = completed
                flag_modified(progress, "quizzes_completed")

        db.commit()
        db.refresh(progress)

        return _build_progress_response(db, org_id, progress)
    finally:
        db.close()


def _get_or_create_progress(db, user_id: str, org_id: str) -> OnboardingProgress:
    # dev-user-001 is not a real UUID — use a deterministic UUID v5 for it
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        uid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)

    progress = (
        db.query(OnboardingProgress)
        .filter(OnboardingProgress.user_id == uid)
        .first()
    )
    if not progress:
        progress = OnboardingProgress(
            id=uuid.uuid4(),
            user_id=uid,
            org_id=uuid.UUID(org_id),
            chapters_read=[],
            quizzes_completed=[],
            quiz_scores={},
            checklist_uses=0,
            chat_queries=0,
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)

    return progress


def _build_progress_response(
    db, org_id: str, progress: OnboardingProgress
) -> OnboardingProgressResponse:
    playbook = _current_playbook(db, org_id)

    total_chapters = 0
    total_quizzes = 0
    if playbook:
        textbook = (
            db.query(TextbookContent)
            .filter(TextbookContent.playbook_id == playbook.id)
            .first()
        )
        if textbook:
            total_chapters = len(textbook.chapters or [])

        quiz_sets = (
            db.query(QuizSet)
            .filter(
                QuizSet.playbook_id == playbook.id,
                QuizSet.quiz_type != "final_assessment",
            )
            .all()
        )
        total_quizzes = len(quiz_sets)

    chapters_read = progress.chapters_read or []
    quiz_scores = progress.quiz_scores or {}
    quizzes_completed = progress.quizzes_completed or []

    quizzes_passed = sum(1 for score in quiz_scores.values() if score == 1.0)

    textbook_pct = len(chapters_read) / total_chapters if total_chapters > 0 else 0.0
    quiz_pct = quizzes_passed / total_quizzes if total_quizzes > 0 else 0.0
    completion_pct = (textbook_pct * 0.5 + quiz_pct * 0.5) * 100

    return OnboardingProgressResponse(
        chapters_read=chapters_read,
        quizzes_completed=[str(qid) for qid in quizzes_completed],
        quiz_scores={str(k): float(v) for k, v in quiz_scores.items()},
        checklist_uses=progress.checklist_uses or 0,
        chat_queries=progress.chat_queries or 0,
        completion_percentage=round(completion_pct, 1),
    )
