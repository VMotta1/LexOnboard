import json
import logging
import time

from anthropic import Anthropic, RateLimitError

from app.config import settings
from app.services.distillation.prompts import SYNTHESIS_SYSTEM_PROMPT, SYNTHESIS_USER_TEMPLATE

logger = logging.getLogger(__name__)

_MODEL = "claude-haiku-4-5-20251001"
_MAX_CLAUSES_PER_CALL = 3
_MAX_CHAR_PER_CLAUSE = 600
_MAX_TOKENS = 2000
_INTER_CALL_DELAY = 5      # seconds between synthesis calls to stay under TPM
_RATE_LIMIT_BACKOFF = 65   # seconds to wait on 429


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
        f"[Clause {i + 1}]\n{_get_text(c)[:_MAX_CHAR_PER_CLAUSE]}" for i, c in enumerate(sample)
    )

    user_content = SYNTHESIS_USER_TEMPLATE.format(
        clause_type=clause_type,
        n_clauses=len(sample),
        clauses_text=clauses_text,
    )

    client = _make_client()

    # First attempt
    raw = _call_claude(client, user_content, extra_user=None)
    if raw is None:
        return None
    result = _try_parse(raw)
    if result is not None:
        return result

    # Single retry with explicit JSON nudge
    logger.warning(f"synthesize_clause_type: JSON parse failed for '{clause_type}', retrying")
    raw = _call_claude(
        client,
        user_content,
        extra_user="Respond with ONLY the JSON object. No markdown, no explanation.",
    )
    if raw is None:
        return None
    result = _try_parse(raw)
    if result is not None:
        return result

    logger.error(f"synthesize_clause_type: JSON parse failed twice for '{clause_type}' — skipping")
    return None


def _get_text(clause) -> str:
    if isinstance(clause, dict):
        return clause.get("raw_text", "")
    return getattr(clause, "raw_text", "")


def _call_claude(client: Anthropic, user_content: str, extra_user: str | None) -> str | None:
    messages = [{"role": "user", "content": user_content}]
    if extra_user:
        messages = [{"role": "user", "content": user_content + "\n\n" + extra_user}]

    for attempt in range(3):
        try:
            response = client.messages.create(
                model=_MODEL,
                max_tokens=_MAX_TOKENS,
                temperature=0,
                system=SYNTHESIS_SYSTEM_PROMPT.strip(),
                messages=messages,
            )
            return response.content[0].text
        except RateLimitError:
            if attempt < 2:
                logger.warning(
                    f"Rate limited — waiting {_RATE_LIMIT_BACKOFF}s before retry "
                    f"(attempt {attempt + 1}/3)"
                )
                time.sleep(_RATE_LIMIT_BACKOFF)
            else:
                logger.error("Rate limit hit 3 times — giving up on this clause type")
                return None
        except Exception as exc:
            logger.error(f"Claude API error: {exc}")
            return None

    return None


def _try_parse(raw: str) -> dict | None:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(line for line in lines if not line.startswith("```"))
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None
