import json
import logging

from anthropic import Anthropic

from app.config import settings
from app.services.distillation.prompts import SYNTHESIS_SYSTEM_PROMPT, SYNTHESIS_USER_TEMPLATE

logger = logging.getLogger(__name__)

_MODEL = "claude-sonnet-4-20250514"
_MAX_CLAUSES_PER_CALL = 20
_MAX_TOKENS = 2000


def _make_client() -> Anthropic:
    return Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def synthesize_clause_type(clause_type: str, clauses: list) -> dict | None:
    """
    Call Claude to distill N examples of a clause type into a PlaybookSection dict.
    Returns None if there are no clauses or if JSON parsing fails after retries.
    clauses: list of ProcessedClause SQLAlchemy objects (or dicts with 'raw_text').
    """
    if not clauses:
        return None

    sample = clauses[:_MAX_CLAUSES_PER_CALL]
    clauses_text = "\n\n---\n\n".join(
        f"[Clause {i + 1}]\n{_get_text(c)}" for i, c in enumerate(sample)
    )

    user_content = SYNTHESIS_USER_TEMPLATE.format(
        clause_type=clause_type,
        n_clauses=len(sample),
        clauses_text=clauses_text,
    )

    client = _make_client()

    # First attempt: temperature 0 for deterministic JSON
    raw = _call_claude(client, user_content, extra_user=None)
    result = _try_parse(raw)
    if result is not None:
        return result

    # Single retry: add explicit JSON reminder
    logger.warning(
        f"synthesize_clause_type: JSON parse failed for '{clause_type}', retrying once"
    )
    raw = _call_claude(
        client,
        user_content,
        extra_user="Respond with ONLY the JSON object. No markdown, no explanation.",
    )
    result = _try_parse(raw)
    if result is not None:
        return result

    logger.error(
        f"synthesize_clause_type: JSON parse failed twice for '{clause_type}' — skipping"
    )
    return None


def _get_text(clause) -> str:
    """Accept both SQLAlchemy model objects and dicts."""
    if isinstance(clause, dict):
        return clause.get("raw_text", "")
    return getattr(clause, "raw_text", "")


def _call_claude(client: Anthropic, user_content: str, extra_user: str | None) -> str:
    messages = [{"role": "user", "content": user_content}]
    if extra_user:
        messages.append({"role": "assistant", "content": "{"})
        messages = [{"role": "user", "content": user_content + "\n\n" + extra_user}]

    response = client.messages.create(
        model=_MODEL,
        max_tokens=_MAX_TOKENS,
        temperature=0,
        system=SYNTHESIS_SYSTEM_PROMPT.strip(),
        messages=messages,
    )
    return response.content[0].text


def _try_parse(raw: str) -> dict | None:
    text = raw.strip()
    # Strip markdown fences if Claude added them despite instructions
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(
            line for line in lines
            if not line.startswith("```")
        )
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None
