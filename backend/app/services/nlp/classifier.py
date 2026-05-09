import logging

logger = logging.getLogger(__name__)

CUAD_LABELS = [
    "Indemnification",
    "Liability Cap",
    "IP Ownership",
    "Confidentiality/NDA",
    "Governing Law",
    "Dispute Resolution",
    "Termination for Convenience",
    "Termination for Cause",
    "Payment Terms",
    "Warranty",
    "Limitation of Liability",
    "Force Majeure",
    "Assignment",
    "Non-Compete/Non-Solicitation",
    "Audit Rights",
    "Insurance",
    "Intellectual Property License",
    "Change Order",
    "Scope of Work",
    "Representations & Warranties",
]

# Longest/most-specific keywords first to avoid partial-match shadowing
_KEYWORD_MAP: list[tuple[str, str]] = [
    ("termination for convenience", "Termination for Convenience"),
    ("terminate for convenience", "Termination for Convenience"),
    ("termination for cause", "Termination for Cause"),
    ("terminate for cause", "Termination for Cause"),
    ("material breach", "Termination for Cause"),
    ("limitation of liability", "Limitation of Liability"),
    ("limit of liability", "Limitation of Liability"),
    ("aggregate liability", "Liability Cap"),
    ("liability cap", "Liability Cap"),
    ("in no event shall", "Limitation of Liability"),
    ("hold harmless", "Indemnification"),
    ("indemnif", "Indemnification"),
    ("non-disclosure", "Confidentiality/NDA"),
    ("proprietary information", "Confidentiality/NDA"),
    ("confidential", "Confidentiality/NDA"),
    ("intellectual property license", "Intellectual Property License"),
    ("grant of rights", "Intellectual Property License"),
    ("work for hire", "IP Ownership"),
    ("ip ownership", "IP Ownership"),
    ("intellectual property", "IP Ownership"),
    ("non-compete", "Non-Compete/Non-Solicitation"),
    ("non-solicitation", "Non-Compete/Non-Solicitation"),
    ("dispute resolution", "Dispute Resolution"),
    ("arbitration", "Dispute Resolution"),
    ("mediation", "Dispute Resolution"),
    ("governing law", "Governing Law"),
    ("applicable law", "Governing Law"),
    ("jurisdiction", "Governing Law"),
    ("force majeure", "Force Majeure"),
    ("act of god", "Force Majeure"),
    ("right to audit", "Audit Rights"),
    ("audit right", "Audit Rights"),
    ("represent and warrant", "Representations & Warranties"),
    ("representations and warranties", "Representations & Warranties"),
    ("warrants and represents", "Representations & Warranties"),
    ("warranty", "Warranty"),
    ("warrants", "Warranty"),
    ("change order", "Change Order"),
    ("statement of work", "Scope of Work"),
    ("scope of work", "Scope of Work"),
    ("deliverable", "Scope of Work"),
    ("payment terms", "Payment Terms"),
    ("net 30", "Payment Terms"),
    ("net 60", "Payment Terms"),
    ("invoice", "Payment Terms"),
    ("insurance", "Insurance"),
    ("assign", "Assignment"),
    ("license", "Intellectual Property License"),
]


class ClauseClassifier:
    _model = None
    _tokenizer = None
    _use_fallback: bool = False

    @classmethod
    def get_model(cls):
        if cls._model is None and not cls._use_fallback:
            try:
                from transformers import (
                    AutoModelForSequenceClassification,
                    AutoTokenizer,
                )

                logger.info(
                    "Loading CUAD-RoBERTa classifier (first use) — ~500MB"
                )
                cls._tokenizer = AutoTokenizer.from_pretrained(
                    "theatticusproject/cuad-roberta"
                )
                cls._model = AutoModelForSequenceClassification.from_pretrained(
                    "theatticusproject/cuad-roberta"
                )
                cls._model.eval()
                logger.info("CUAD-RoBERTa classifier loaded.")
            except Exception as exc:
                logger.warning(
                    f"Could not load CUAD-RoBERTa ({exc}). "
                    "Falling back to keyword-based classification."
                )
                cls._use_fallback = True

        return cls._model

    @classmethod
    def classify(cls, text: str) -> tuple[str, float]:
        """Return (clause_type, confidence). Falls back to keyword matching if model unavailable."""
        model = cls.get_model()

        if model is not None and not cls._use_fallback:
            try:
                import torch
                import torch.nn.functional as F

                inputs = cls._tokenizer(
                    text[:512],
                    return_tensors="pt",
                    truncation=True,
                    max_length=512,
                )
                with torch.no_grad():
                    logits = model(**inputs).logits

                probs = F.softmax(logits, dim=-1)
                confidence, predicted_idx = probs.max(dim=-1)
                confidence_val = float(confidence.item())

                label_map = getattr(model.config, "id2label", {})
                clause_type = label_map.get(int(predicted_idx.item()), "unclassified")

                if confidence_val < 0.5:
                    clause_type = "unclassified"

                return clause_type, confidence_val

            except Exception as exc:
                logger.warning(f"Classifier forward pass failed: {exc}. Using keyword fallback.")

        return cls._keyword_classify(text)

    @classmethod
    def _keyword_classify(cls, text: str) -> tuple[str, float]:
        lower = text.lower()
        for keyword, label in _KEYWORD_MAP:
            if keyword in lower:
                return label, 0.7
        return "unclassified", 0.0