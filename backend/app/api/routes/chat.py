import logging
import uuid

from fastapi import APIRouter, HTTPException, Request

from app.api.deps import get_org_id, get_user_context
from app.database import SessionLocal
from app.models.onboarding import ChatMessage, OnboardingProgress
from app.schemas.chat import ChatQueryRequest, ChatResponse, SourceClause

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

_MAX_QUESTION_LEN = 500
_MAX_HISTORY_TURNS = 10


@router.post("/query", response_model=ChatResponse)
async def query_chat(request: Request, body: ChatQueryRequest):
    # TODO: replace get_user_context with real auth when auth is implemented
    ctx = get_user_context(request)
    org_id = ctx["org_id"]
    user_id = ctx["user_id"]

    # Validate inputs
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="question must not be empty")
    if len(body.question) > _MAX_QUESTION_LEN:
        raise HTTPException(
            status_code=400,
            detail=f"question exceeds {_MAX_QUESTION_LEN} character limit",
        )
    if len(body.conversation_history) > _MAX_HISTORY_TURNS:
        raise HTTPException(
            status_code=400,
            detail=f"conversation_history exceeds {_MAX_HISTORY_TURNS} turns",
        )

    from app.services.retrieval.chat_service import answer_question

    result = answer_question(
        question=body.question,
        org_id=org_id,
        conversation_history=body.conversation_history,
        session_id=body.session_id,
        user_id=user_id,
    )

    # Increment chat_queries counter for this user (fire-and-forget style)
    _increment_chat_queries(user_id, org_id)

    return ChatResponse(
        answer=result["answer"],
        sources=[SourceClause(**s) for s in result["sources"]],
        session_id=result["session_id"],
    )


@router.get("/history")
async def get_chat_history(request: Request, session_id: str):
    # TODO: replace get_user_context with real auth when auth is implemented
    ctx = get_user_context(request)
    org_id = ctx["org_id"]

    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        sid = uuid.uuid5(uuid.NAMESPACE_DNS, session_id)

    db = SessionLocal()
    try:
        messages = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.session_id == sid,
                ChatMessage.org_id == uuid.UUID(org_id),
            )
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
        return [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "source_clause_ids": m.source_clause_ids or [],
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ]
    finally:
        db.close()


def _increment_chat_queries(user_id: str, org_id: str) -> None:
    """Increment OnboardingProgress.chat_queries — best-effort, never raises."""
    try:
        try:
            uid = uuid.UUID(user_id)
        except (ValueError, AttributeError):
            uid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)

        db = SessionLocal()
        try:
            progress = (
                db.query(OnboardingProgress)
                .filter(OnboardingProgress.user_id == uid)
                .first()
            )
            if progress:
                progress.chat_queries = (progress.chat_queries or 0) + 1
                db.commit()
        finally:
            db.close()
    except Exception as exc:
        logger.warning(f"Failed to increment chat_queries for {user_id}: {exc}")
