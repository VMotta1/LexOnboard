import json
import logging
import time
from collections import defaultdict

from anthropic import Anthropic, RateLimitError

from app.config import settings
from app.services.generation.prompts import CHECKLIST_GENERATION_PROMPT

logger = logging.getLogger(__name__)

_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 2000
_INTER_CALL_DELAY = 3
_RATE_LIMIT_BACKOFF = 65


def _client() -> Anthropic:
    return Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def generate_checklist(playbook) -> dict:
    """
    Generate a ContractChecklist from an OrgPlaybook.
    Calls Claude once per section so each checklist item embeds actual extracted_values.
    Returns dict matching ContractChecklist DB structure.
    """
    sections = playbook.sections or []
    claude = _client()
    all_items: list[dict] = []

    for i, section in enumerate(sections):
        if i > 0:
            time.sleep(_INTER_CALL_DELAY)

        section_json = json.dumps(
            {
                "clause_type": section.get("clause_type", ""),
                "title": section.get("title", ""),
                "non_negotiables": section.get("non_negotiables", []),
                "standard_positions": section.get("standard_positions", []),
                "red_flags": section.get("red_flags", []),
                "extracted_values": section.get("extracted_values", {}),
            },
            indent=2,
        )

        prompt = CHECKLIST_GENERATION_PROMPT.format(section_json=section_json)
        items = _generate_section_items(claude, section.get("clause_type", "unknown"), prompt)
        all_items.extend(items)

    if not all_items:
        logger.error("Checklist generation produced no items — returning fallback")
        return {"categories": _fallback_categories(sections)}

    # Group flat items by category field
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in all_items:
        cat = item.get("category") or "Key Clause Checklist"
        grouped[cat].append(item)

    categories = [{"category": cat, "items": items} for cat, items in grouped.items()]
    return {"categories": categories}


def _generate_section_items(claude: Anthropic, clause_type: str, prompt: str) -> list[dict]:
    for attempt in range(3):
        try:
            response = claude.messages.create(
                model=_MODEL,
                max_tokens=_MAX_TOKENS,
                temperature=0,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = "\n".join(line for line in raw.splitlines() if not line.startswith("```"))
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return parsed
            logger.warning(f"Checklist section '{clause_type}': expected list, got {type(parsed)}")
            return []
        except RateLimitError:
            if attempt < 2:
                logger.warning(f"Rate limited on '{clause_type}' — waiting {_RATE_LIMIT_BACKOFF}s")
                time.sleep(_RATE_LIMIT_BACKOFF)
            else:
                logger.error(f"Rate limit hit 3 times on '{clause_type}' — skipping")
                return []
        except Exception as exc:
            logger.warning(f"Checklist section '{clause_type}' attempt {attempt + 1} failed: {exc}")
            return []
    return []


def _fallback_categories(sections: list[dict]) -> list[dict]:
    items = [
        {
            "item": f"Review the {s.get('clause_type', 'General')} clause — no specific values extracted",
            "category": "Key Clause Checklist",
            "risk_level": "medium",
            "contract_value": "not extracted",
            "is_mandatory": bool(s.get("non_negotiables")),
        }
        for s in sections
    ] or [
        {
            "item": "Review the contract against org standards — generation failed",
            "category": "Key Clause Checklist",
            "risk_level": "medium",
            "contract_value": "not extracted",
            "is_mandatory": False,
        }
    ]
    return [{"category": "Key Clause Checklist", "items": items}]
