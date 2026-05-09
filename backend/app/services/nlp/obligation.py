import logging

logger = logging.getLogger(__name__)

_MODAL_WORDS = frozenset({"shall", "must", "will", "may"})
_MODAL_PHRASES = ("agrees to", "is required to", "is obligated to")
_MANDATORY_MODALS = frozenset({"shall", "must", "is required to", "is obligated to"})

_spacy_model = None


def _get_spacy_model():
    global _spacy_model
    if _spacy_model is None:
        import spacy

        try:
            _spacy_model = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("en_core_web_sm not found — downloading")
            from spacy.cli import download as spacy_download

            spacy_download("en_core_web_sm")
            _spacy_model = spacy.load("en_core_web_sm")
    return _spacy_model


def _find_subject(verb_token) -> str:
    """Return the nominal subject of a verb as a string."""
    for child in verb_token.children:
        if child.dep_ in ("nsubj", "nsubjpass"):
            parts = [
                t.text
                for t in child.subtree
                if t.dep_ in ("compound", "nsubj", "nsubjpass", "amod") or t == child
            ]
            return " ".join(parts)[:100]
    return "party"


def _find_action(modal_token, head_token) -> str:
    """Extract the main action phrase from modal + head verb."""
    parts = [head_token.text]
    for child in head_token.children:
        if child.dep_ in ("dobj", "xcomp", "ccomp", "prep") and child != modal_token:
            parts.append(child.text)
            for grandchild in child.children:
                if grandchild.dep_ in ("pobj", "dobj"):
                    parts.append(grandchild.text)
                    break
    return " ".join(parts)[:200]


def extract_obligations(text: str) -> list[dict]:
    """
    Extract (party, modal, action, is_mandatory) obligation tuples via spaCy dep parse.
    Returns [] on any failure — never raises.
    """
    try:
        nlp = _get_spacy_model()
        doc = nlp(text)
        obligations: list[dict] = []

        for sent in doc.sents:
            sent_lower = sent.text.lower()

            # Quick filter before full dep parse traversal
            has_modal = any(m in sent_lower for m in _MODAL_WORDS) or any(
                p in sent_lower for p in _MODAL_PHRASES
            )
            if not has_modal:
                continue

            for token in sent:
                if token.text.lower() not in _MODAL_WORDS:
                    continue

                modal = token.text.lower()
                head = token.head
                subject = _find_subject(head)
                action = _find_action(token, head)
                is_mandatory = modal in _MANDATORY_MODALS

                obligations.append(
                    {
                        "party": subject,
                        "modal": modal,
                        "action": action,
                        "is_mandatory": is_mandatory,
                    }
                )

                if len(obligations) >= 10:
                    return obligations

        return obligations

    except Exception as exc:
        logger.warning(f"Obligation extraction failed: {exc}")
        return []