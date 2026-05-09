import json
import logging
import random
import time
import uuid

from anthropic import Anthropic, RateLimitError

from app.config import settings
from app.services.generation.prompts import QUIZ_GENERATION_TEMPLATE

logger = logging.getLogger(__name__)

_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 1500
_RATE_LIMIT_BACKOFF = 65

# Clause types prioritised for the final assessment
_PRIORITY_TYPES = [
    "Indemnification",
    "Liability Cap",
    "IP Ownership",
    "Governing Law",
    "Termination for Cause",
    "Confidentiality/NDA",
    "Payment Terms",
    "Limitation of Liability",
]


def _client() -> Anthropic:
    return Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def generate_quiz_for_chapter(chapter: dict, playbook_section: dict) -> dict:
    """
    Generate a QuizSet for one textbook chapter.
    Returns a dict matching the QuizSet DB structure.
    """
    clause_type = chapter.get("clause_type") or playbook_section.get("clause_type", "General")
    section_title = playbook_section.get("title", clause_type)
    example_clauses = "\n\n".join(playbook_section.get("example_clauses", [])[:3])

    prompt = QUIZ_GENERATION_TEMPLATE.format(
        chapter_num=chapter.get("chapter_number", 1),
        section_title=section_title,
        chapter_content=chapter.get("content", "")[:3000],
        example_clauses=example_clauses or "(No example clauses available)",
        clause_type=clause_type,
    )

    claude = _client()
    questions = _fallback_questions(clause_type)
    for attempt in range(3):
        try:
            response = claude.messages.create(
                model=_MODEL,
                max_tokens=_MAX_TOKENS,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = "\n".join(line for line in raw.splitlines() if not line.startswith("```"))
            questions_raw = json.loads(raw)
            questions = [_normalise_question(q, clause_type) for q in questions_raw]
            break
        except RateLimitError:
            if attempt < 2:
                logger.warning(f"Quiz rate limited for '{section_title}' — waiting {_RATE_LIMIT_BACKOFF}s")
                time.sleep(_RATE_LIMIT_BACKOFF)
            else:
                logger.error(f"Quiz failed 3× rate limit for '{section_title}' — using fallback")
        except Exception as exc:
            logger.warning(f"Quiz generation failed for '{section_title}': {exc}")
            break

    return {
        "id": str(uuid.uuid4()),
        "quiz_type": "chapter_review",
        "chapter_index": chapter.get("chapter_number"),
        "questions": questions,
    }


def generate_final_assessment(
    chapter_quizzes: list[dict],
    all_sections: list[dict],
) -> dict:
    """
    Build a 10-question final assessment by selecting 2 questions from each of the
    5 most important clause types. Draws from already-generated chapter quizzes.
    """
    # Build index: clause_type → list of questions
    by_type: dict[str, list] = {}
    for quiz in chapter_quizzes:
        for q in quiz.get("questions", []):
            ct = q.get("clause_type", "General")
            by_type.setdefault(ct, []).append(q)

    selected: list[dict] = []

    # Pick 2 from each priority type (up to 5 types → 10 questions)
    used_types = 0
    for ptype in _PRIORITY_TYPES:
        if used_types >= 5:
            break
        pool = by_type.get(ptype, [])
        if not pool:
            continue
        pick = random.sample(pool, min(2, len(pool)))
        selected.extend(pick)
        used_types += 1

    # If we didn't hit 10, fill from remaining types
    if len(selected) < 10:
        remaining = [
            q for ct, qs in by_type.items()
            if ct not in _PRIORITY_TYPES
            for q in qs
        ]
        random.shuffle(remaining)
        selected.extend(remaining[: 10 - len(selected)])

    # Give each question a fresh id to avoid collisions
    final_questions = [
        {**q, "id": str(uuid.uuid4())} for q in selected[:10]
    ]

    return {
        "id": str(uuid.uuid4()),
        "quiz_type": "final_assessment",
        "chapter_index": None,
        "questions": final_questions,
    }


def _normalise_question(raw: dict, fallback_clause_type: str) -> dict:
    """Ensure every question dict has an id and required fields."""
    return {
        "id": str(uuid.uuid4()),
        "question_type": raw.get("question_type", "mcq"),
        "text": raw.get("text", ""),
        "context": raw.get("context"),
        "options": raw.get("options"),
        "correct_answer": raw.get("correct_answer", ""),
        "explanation": raw.get("explanation", ""),
        "clause_type": raw.get("clause_type", fallback_clause_type),
    }


def _fallback_questions(clause_type: str) -> list[dict]:
    """Minimal fallback if Claude call fails — ensures quiz set is non-empty."""
    return [
        {
            "id": str(uuid.uuid4()),
            "question_type": "true_false",
            "text": f"Understanding {clause_type} clauses is important for contract review.",
            "context": None,
            "options": ["True", "False"],
            "correct_answer": "True",
            "explanation": f"{clause_type} clauses define key obligations and must be reviewed carefully.",
            "clause_type": clause_type,
        }
    ]
