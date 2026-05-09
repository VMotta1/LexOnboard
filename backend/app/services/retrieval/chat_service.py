import logging
import uuid

from anthropic import Anthropic

from app.config import settings
from app.database import SessionLocal
from app.models.onboarding import ChatMessage
from app.services.retrieval.retriever import retrieve_relevant_clauses

logger = logging.getLogger(__name__)

_MODEL = "claude-sonnet-4-20250514"
_MAX_TOKENS = 1500
_HISTORY_TURNS = 4   # last 4 messages (2 user + 2 assistant)

CHAT_SYSTEM_PROMPT = """
You are a legal knowledge assistant for a specific organization. You have access to this \
organization's actual contract history, distilled into a knowledge base. When answering \
questions from new hires, you:

1. Ground every answer in the retrieved contract clauses provided to you
2. Cite your sources: reference the clause type and section when stating a position
3. Distinguish clearly between: (a) this org's non-negotiables, (b) their standard positions, \
(c) acceptable variations, and (d) general legal practice
4. If the retrieved clauses don't cover the question, say so — don't invent positions
5. Keep answers practical: what should this person actually DO with this information?

You are NOT a licensed attorney and this is NOT legal advice. You are explaining how this \
organization has historically handled contract matters based on their actual documents.
"""


def _client() -> Anthropic:
    return Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def answer_question(
    question: str,
    org_id: str,
    conversation_history: list[dict],
    session_id: str,
    user_id: str = "dev-user-001",
) -> dict:
    """
    RAG chat: embed question → retrieve top-5 clauses → Claude answer → persist messages.
    Returns {answer, sources, session_id}.
    """
    # 1. Retrieve relevant clauses
    retrieved = retrieve_relevant_clauses(question, org_id, top_k=5)

    # 2. Build context block
    if retrieved:
        context_parts = [
            f"[Source {i + 1}: {c['clause_type']} — {' > '.join(c['section_path'])}]\n{c['raw_text']}"
            for i, c in enumerate(retrieved)
        ]
        context = "\n\n".join(context_parts)
    else:
        context = "(No relevant contract clauses found for this question.)"

    # 3. Build messages: last 4 history turns + new user message with context
    history_slice = conversation_history[-_HISTORY_TURNS:]
    messages = list(history_slice)
    messages.append(
        {
            "role": "user",
            "content": (
                f"Based on our organization's contract clauses:\n\n{context}"
                f"\n\nQuestion: {question}"
            ),
        }
    )

    # 4. Call Claude API (non-streaming)
    claude = _client()
    response = claude.messages.create(
        model=_MODEL,
        max_tokens=_MAX_TOKENS,
        temperature=0.3,
        system=CHAT_SYSTEM_PROMPT.strip(),
        messages=messages,
    )
    answer_text = response.content[0].text

    # 5. Persist ChatMessage records
    _persist_messages(
        org_id=org_id,
        user_id=user_id,
        session_id=session_id,
        question=question,
        answer=answer_text,
        source_clause_ids=[c["id"] for c in retrieved],
    )

    # 6. Build source cards (first 200 chars of each clause as excerpt)
    sources = [
        {
            "id": c["id"],
            "clause_type": c["clause_type"],
            "section_path": c["section_path"],
            "excerpt": c["raw_text"][:200] + ("…" if len(c["raw_text"]) > 200 else ""),
        }
        for c in retrieved
    ]

    return {"answer": answer_text, "sources": sources, "session_id": session_id}


def _coerce_uuid(value: str) -> uuid.UUID:
    """Parse value as UUID; fall back to deterministic UUID v5."""
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError):
        return uuid.uuid5(uuid.NAMESPACE_DNS, value)


def _persist_messages(
    org_id: str,
    user_id: str,
    session_id: str,
    question: str,
    answer: str,
    source_clause_ids: list[str],
) -> None:
    uid = _coerce_uuid(user_id)
    sid = _coerce_uuid(session_id)
    oid = uuid.UUID(org_id)

    db = SessionLocal()
    try:
        user_msg = ChatMessage(
            id=uuid.uuid4(),
            session_id=sid,
            user_id=uid,
            org_id=oid,
            role="user",
            content=question,
            source_clause_ids=[],
        )
        assistant_msg = ChatMessage(
            id=uuid.uuid4(),
            session_id=sid,
            user_id=uid,
            org_id=oid,
            role="assistant",
            content=answer,
            source_clause_ids=source_clause_ids,
        )
        db.add(user_msg)
        db.add(assistant_msg)
        db.commit()
    except Exception as exc:
        logger.warning(f"Failed to persist chat messages: {exc}")
        db.rollback()
    finally:
        db.close()
