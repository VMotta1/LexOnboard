import logging

logger = logging.getLogger(__name__)


class NERService:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            from transformers import pipeline as hf_pipeline

            logger.info(
                "Loading LegalBERT NER model (first use) — ~400MB, may take a moment"
            )
            cls._model = hf_pipeline(
                "ner",
                model="nlpaueb/legal-bert-base-uncased",
                aggregation_strategy="simple",
                device=-1,  # CPU
            )
            logger.info("LegalBERT NER model loaded.")
        return cls._model

    @classmethod
    def extract_entities(cls, text: str) -> dict:
        """Extract named entities. Returns empty dict on failure — never raises."""
        try:
            model = cls.get_model()
            # BERT max sequence length is 512 tokens; ~2000 chars is a safe proxy
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

                if label in ("ORG", "PER"):
                    if word not in entities["parties"]:
                        entities["parties"].append(word)
                elif label == "DATE":
                    if word not in entities["dates"]:
                        entities["dates"].append(word)
                elif label in ("MONEY", "PERCENT"):
                    if word not in entities["amounts"]:
                        entities["amounts"].append(word)
                elif label in ("GPE", "LOC", "LAW"):
                    if word not in entities["jurisdictions"]:
                        entities["jurisdictions"].append(word)

            return entities

        except Exception as exc:
            logger.warning(f"NER failed — returning empty entities. Reason: {exc}")
            return {
                "parties": [],
                "dates": [],
                "amounts": [],
                "jurisdictions": [],
                "defined_terms": [],
            }