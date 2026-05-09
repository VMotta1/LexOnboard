import logging

logger = logging.getLogger(__name__)


class NERService:
    _model = None
    _use_fallback: bool = False

    @classmethod
    def get_model(cls):
        if cls._model is None and not cls._use_fallback:
            try:
                from transformers import pipeline as hf_pipeline

                logger.info("Loading bert-base-NER model (first use) — ~400MB")
                cls._model = hf_pipeline(
                    "ner",
                    model="dslim/bert-base-NER",
                    aggregation_strategy="simple",
                    device=-1,
                )
                logger.info("NER model loaded.")
            except Exception as exc:
                logger.warning(
                    f"Could not load NER model ({exc}). Falling back to regex NER."
                )
                cls._use_fallback = True
        return cls._model

    @classmethod
    def extract_entities(cls, text: str) -> dict:
        """Extract named entities. Returns empty dict on failure — never raises."""
        model = cls.get_model()
        if model is not None and not cls._use_fallback:
            try:
                results = model(text[:2000])
                entities: dict = {
                    "parties": [],
                    "dates": [],
                    "amounts": [],
                    "jurisdictions": [],
                    "defined_terms": [],
                }
                for entity in results:
                    label = entity.get("entity_group", "")
                    word = entity.get("word", "").strip()
                    if not word:
                        continue
                    if label in ("ORG", "PER") and word not in entities["parties"]:
                        entities["parties"].append(word)
                    elif label == "DATE" and word not in entities["dates"]:
                        entities["dates"].append(word)
                    elif label in ("MONEY", "PERCENT") and word not in entities["amounts"]:
                        entities["amounts"].append(word)
                    elif label in ("GPE", "LOC") and word not in entities["jurisdictions"]:
                        entities["jurisdictions"].append(word)
                return entities
            except Exception as exc:
                logger.warning(f"NER model inference failed: {exc}. Using regex fallback.")

        return _regex_entities(text)


def _regex_entities(text: str) -> dict:
    """Regex-based entity extraction fallback — no external dependencies."""
    import re

    entities: dict = {
        "parties": [],
        "dates": [],
        "amounts": [],
        "jurisdictions": [],
        "defined_terms": [],
    }

    # Dates: "30 days", "January 1, 2025", "2025-01-01"
    dates = re.findall(
        r'\b(?:\d{1,2}\s+(?:days?|months?|years?)|'
        r'(?:January|February|March|April|May|June|July|August|September|October|November|December)'
        r'\s+\d{1,2},?\s+\d{4}|'
        r'\d{4}-\d{2}-\d{2})\b',
        text,
        re.IGNORECASE,
    )
    entities["dates"] = list(dict.fromkeys(dates))[:5]

    # Amounts: "$1,000,000", "USD 500,000", "10%"
    amounts = re.findall(
        r'\b(?:USD\s+[\d,]+(?:\.\d+)?(?:\s*(?:million|billion|thousand))?'
        r'|\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion|thousand))?'
        r'|\d+(?:\.\d+)?\s*%)\b',
        text,
        re.IGNORECASE,
    )
    entities["amounts"] = list(dict.fromkeys(amounts))[:5]

    # Defined terms: words/phrases in quotes or Title Case in parentheses
    defined = re.findall(r'"([A-Z][^"]{2,40})"', text)
    defined += re.findall(r'\((?:the\s+)?"([A-Z][a-zA-Z\s]{2,30})"\)', text)
    entities["defined_terms"] = list(dict.fromkeys(defined))[:10]

    return entities
