import json
import logging
import time

from anthropic import Anthropic, RateLimitError

from app.config import settings
from app.services.generation.prompts import TEXTBOOK_CHAPTER_TEMPLATE, TEXTBOOK_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS_PER_CHAPTER = 1000
_MAX_SECTIONS = 8  # page budget cap
_INTER_CHAPTER_DELAY = 20   # seconds between chapters to stay under 4k output TPM
_RATE_LIMIT_BACKOFF = 65    # seconds to wait on 429


def _client() -> Anthropic:
    return Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def generate_textbook(playbook, org_name: str = "Your Organization") -> dict:
    """
    Generate a full textbook from an OrgPlaybook.
    playbook: OrgPlaybook SQLAlchemy model (playbook.sections is a list of dicts).
    Returns {chapters: list[dict], page_estimate: int}.
    """
    sections = playbook.sections or []
    chapters = []

    # Chapter 0: hardcoded introduction
    chapters.append(_intro_chapter(org_name, sections))

    claude = _client()

    for i, section in enumerate(sections[:_MAX_SECTIONS]):
        chapter_num = i + 1
        if i > 0:
            time.sleep(_INTER_CHAPTER_DELAY)
        chapter = _generate_chapter_with_retry(claude, chapter_num, section)
        chapters.append(chapter)

    # Final chapter: aggregated red flags summary (hardcoded, no Claude call)
    chapters.append(_red_flags_summary(len(chapters), sections))

    return {
        "chapters": chapters,
        "page_estimate": _estimate_pages(chapters),
    }


def _generate_chapter_with_retry(claude: Anthropic, chapter_num: int, section: dict) -> dict:
    for attempt in range(3):
        try:
            return _generate_chapter(claude, chapter_num, section)
        except RateLimitError:
            if attempt < 2:
                logger.warning(f"Chapter {chapter_num} rate limited — waiting {_RATE_LIMIT_BACKOFF}s")
                time.sleep(_RATE_LIMIT_BACKOFF)
            else:
                logger.error(f"Chapter {chapter_num} failed after 3 rate limit retries — using placeholder")
        except Exception as exc:
            logger.warning(f"Chapter {chapter_num} ({section.get('clause_type')}) failed: {exc}")
            break
    return {
        "title": section.get("title", section.get("clause_type", "Unknown")),
        "chapter_number": chapter_num,
        "content": "_Content unavailable — generation error._",
        "key_takeaways": [],
        "clause_type": section.get("clause_type"),
        "quiz_id": None,
    }


def _generate_chapter(claude: Anthropic, chapter_num: int, section: dict) -> dict:
    clause_type = section.get("clause_type", "General")
    section_title = section.get("title", clause_type)
    section_json = json.dumps(
        {k: v for k, v in section.items() if k != "example_clauses"},
        indent=2,
    )

    prompt = TEXTBOOK_CHAPTER_TEMPLATE.format(
        chapter_num=chapter_num,
        clause_type=clause_type,
        section_title=section_title,
        playbook_section_json=section_json,
    )

    response = claude.messages.create(
        model=_MODEL,
        max_tokens=_MAX_TOKENS_PER_CHAPTER,
        system=TEXTBOOK_SYSTEM_PROMPT.strip(),
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text

    # Split on KEY_TAKEAWAYS: delimiter
    if "KEY_TAKEAWAYS:" in raw:
        body, _, takeaway_block = raw.partition("KEY_TAKEAWAYS:")
        takeaways = [
            line.lstrip("- ").strip()
            for line in takeaway_block.strip().splitlines()
            if line.strip().startswith("-")
        ]
    else:
        body = raw
        takeaways = []

    return {
        "title": section_title,
        "chapter_number": chapter_num,
        "content": body.strip(),
        "key_takeaways": takeaways[:3],
        "clause_type": clause_type,
        "quiz_id": None,
    }


def _intro_chapter(org_name: str, sections: list[dict]) -> dict:
    covered = ", ".join(s.get("title", s.get("clause_type", "")) for s in sections[:6])
    content = (
        f"## Welcome to {org_name}'s Contract Framework\n\n"
        "This guide is your practical introduction to how contracts work at this organization. "
        "It's not a law school textbook — it's a field guide written specifically for how "
        f"{org_name} operates.\n\n"
        "### What You'll Learn\n\n"
        f"This guide covers the clause types that appear most often in our contracts: {covered}. "
        "For each topic, you'll learn what matters to us, what to flag, and what never to accept.\n\n"
        "### How to Use This Guide\n\n"
        "- Read each chapter before reviewing any real contract.\n"
        "- Complete the quiz at the end of each chapter — you must score 100% to proceed.\n"
        "- Use the Contract Review Checklist when working through any new agreement.\n"
        "- Ask the Playbook chatbot when you need a quick answer based on our actual contracts.\n\n"
        "### Important Note\n\n"
        "This guide reflects how this organization has historically handled contracts. "
        "It is not legal advice. Always escalate unusual clauses to the legal team."
    )
    return {
        "title": f"Welcome to {org_name}'s Contract Framework",
        "chapter_number": 0,
        "content": content,
        "key_takeaways": [
            "This guide is based on our actual contracts, not generic legal theory.",
            "You must score 100% on each chapter quiz to complete onboarding.",
            "When in doubt, escalate to the legal team — this guide helps you know when.",
        ],
        "clause_type": None,
        "quiz_id": None,
    }


def _red_flags_summary(chapter_num: int, sections: list[dict]) -> dict:
    lines = []
    for section in sections:
        flags = section.get("red_flags", [])
        if not flags:
            continue
        title = section.get("title", section.get("clause_type", "Unknown"))
        lines.append(f"### {title}\n")
        lines.extend(f"- {flag}" for flag in flags)
        lines.append("")

    content = (
        "## Red Flags: Quick Reference\n\n"
        "The following patterns should trigger an immediate review escalation. "
        "If you see any of these in a contract, stop and flag it before proceeding.\n\n"
        + ("\n".join(lines) if lines else "_No specific red flags defined in this playbook._")
    )

    return {
        "title": "Red Flags & Common Mistakes",
        "chapter_number": chapter_num,
        "content": content,
        "key_takeaways": [
            "Red flags do not mean reject — they mean escalate.",
            "Always document why you flagged a clause.",
            "When uncertain, the cost of asking is always lower than the cost of signing.",
        ],
        "clause_type": None,
        "quiz_id": None,
    }


def _estimate_pages(chapters: list[dict]) -> int:
    total_words = sum(len(c.get("content", "").split()) for c in chapters)
    return min(20, max(10, total_words // 350))
