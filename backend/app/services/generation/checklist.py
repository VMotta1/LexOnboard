import json
import logging

from anthropic import Anthropic

from app.config import settings
from app.services.generation.prompts import CHECKLIST_GENERATION_PROMPT

logger = logging.getLogger(__name__)

_MODEL = "claude-sonnet-4-20250514"
_MAX_TOKENS = 4000
_MIN_CATEGORIES = 3


def _client() -> Anthropic:
    return Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def generate_checklist(playbook) -> dict:
    """
    Generate a ContractChecklist from an OrgPlaybook.
    playbook: OrgPlaybook SQLAlchemy model.
    Returns dict matching ContractChecklist DB structure.
    """
    sections = playbook.sections or []

    # Summarised playbook: only non_negotiables + clause types to keep token count manageable
    summary = {
        "sections": [
            {
                "clause_type": s.get("clause_type", ""),
                "title": s.get("title", ""),
                "non_negotiables": s.get("non_negotiables", []),
            }
            for s in sections
        ]
    }
    playbook_json = json.dumps(summary, indent=2)

    prompt = CHECKLIST_GENERATION_PROMPT.format(playbook_json=playbook_json)
    claude = _client()

    for attempt in range(2):
        try:
            response = claude.messages.create(
                model=_MODEL,
                max_tokens=_MAX_TOKENS,
                temperature=0,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()

            # Strip markdown fences
            if raw.startswith("```"):
                raw = "\n".join(
                    line for line in raw.splitlines() if not line.startswith("```")
                )

            parsed = json.loads(raw)
            categories = parsed.get("categories", [])

            if len(categories) >= _MIN_CATEGORIES:
                return {"categories": categories}

            logger.warning(
                f"Checklist attempt {attempt + 1}: only {len(categories)} categories "
                f"(need >= {_MIN_CATEGORIES}), retrying"
            )
            prompt += "\n\nIMPORTANT: You must include at least 9 categories. Return ONLY valid JSON."

        except Exception as exc:
            logger.warning(f"Checklist generation attempt {attempt + 1} failed: {exc}")

    logger.error("Checklist generation failed after 2 attempts — returning minimal fallback")
    return {"categories": _fallback_categories(sections)}


def _fallback_categories(sections: list[dict]) -> list[dict]:
    """Minimal deterministic checklist when Claude generation fails."""
    items = []
    for s in sections:
        clause_type = s.get("clause_type", "General")
        items.append({
            "item_clause": s.get("title", clause_type),
            "review_question": f"Have you reviewed the {clause_type} clause against org standards?",
            "is_non_negotiable": bool(s.get("non_negotiables")),
            "clause_type": clause_type,
        })

    return [
        {
            "name": "I. Contract Standards Review",
            "subcategories": [
                {
                    "name": "A. Key Clause Checklist",
                    "items": items or [
                        {
                            "item_clause": "General Review",
                            "review_question": "Has the contract been reviewed against org standards?",
                            "is_non_negotiable": False,
                            "clause_type": "General",
                        }
                    ],
                }
            ],
        }
    ]
