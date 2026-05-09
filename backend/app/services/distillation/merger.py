from datetime import datetime, timezone

# Canonical section display order (Parties → Scope → Time → Payment → Liability → IP → Termination → Law → Other)
_SECTION_ORDER = [
    "Scope of Work",
    "Payment Terms",
    "Representations & Warranties",
    "Warranty",
    "Indemnification",
    "Liability Cap",
    "Limitation of Liability",
    "Insurance",
    "IP Ownership",
    "Intellectual Property License",
    "Confidentiality/NDA",
    "Non-Compete/Non-Solicitation",
    "Termination for Convenience",
    "Termination for Cause",
    "Force Majeure",
    "Assignment",
    "Governing Law",
    "Dispute Resolution",
    "Audit Rights",
    "Change Order",
]

_ORDER_MAP = {label: i for i, label in enumerate(_SECTION_ORDER)}


def merge_into_playbook(
    org_id: str,
    sections: list[dict],
    doc_count: int,
    next_version: int,
) -> dict:
    """
    Combine PlaybookSection dicts into an OrgPlaybook dict ready for DB insertion.
    Filters None entries, sorts by canonical display order.
    """
    valid = [s for s in sections if s is not None]

    valid.sort(
        key=lambda s: _ORDER_MAP.get(s.get("clause_type", ""), len(_SECTION_ORDER))
    )

    return {
        "org_id": org_id,
        "version": next_version,
        "is_current": True,
        "sections": valid,
        "doc_count": doc_count,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "onboarding_ready": False,
    }
