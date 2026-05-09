import logging
import re

logger = logging.getLogger(__name__)

_MODAL_PATTERN = re.compile(
    r'\b(shall|must|will|may|agrees?\s+to|is\s+required\s+to|is\s+obligated\s+to)\b',
    re.IGNORECASE,
)
_MANDATORY_MODALS = {"shall", "must", "is required to", "is obligated to", "agrees to"}

# Split on sentence boundaries (period/semicolon followed by whitespace + capital)
_SENT_SPLIT = re.compile(r'(?<=[.;])\s+(?=[A-Z])')


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_SPLIT.split(text) if s.strip()]


def _extract_subject(sentence: str, modal_start: int) -> str:
    before = sentence[:modal_start].strip()
    # Take last 6 words before modal as subject proxy
    words = before.split()
    subject = " ".join(words[-6:]) if words else "party"
    return subject[:100] or "party"


def _extract_action(sentence: str, modal_end: int) -> str:
    after = sentence[modal_end:].strip()
    # Take up to 10 words after modal as action
    words = after.split()
    return " ".join(words[:10])[:200]


def extract_obligations(text: str) -> list[dict]:
    """
    Extract obligation tuples via regex. Returns [] on failure — never raises.
    """
    try:
        sentences = _split_sentences(text)
        obligations: list[dict] = []

        for sentence in sentences:
            for match in _MODAL_PATTERN.finditer(sentence):
                modal_raw = match.group(0)
                modal = modal_raw.lower().strip()
                is_mandatory = any(m in modal for m in _MANDATORY_MODALS)

                subject = _extract_subject(sentence, match.start())
                action = _extract_action(sentence, match.end())

                if not action:
                    continue

                obligations.append({
                    "party": subject,
                    "modal": modal,
                    "action": action,
                    "is_mandatory": is_mandatory,
                })

                if len(obligations) >= 10:
                    return obligations

        return obligations

    except Exception as exc:
        logger.warning(f"Obligation extraction failed: {exc}")
        return []
