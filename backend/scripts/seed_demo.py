#!/usr/bin/env python3
"""
Demo seed script — populates DB + Qdrant with Ironbridge Engineering Ltd. fixtures.
Run: python backend/scripts/seed_demo.py
Requires: DB running, Qdrant running, ANTHROPIC_API_KEY not needed for seeding.
"""
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Ensure app package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/lexonboard")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("ANTHROPIC_API_KEY", "demo-placeholder")

from app.config import settings  # noqa: E402
from app.database import SessionLocal, Base, engine  # noqa: E402
from app.models.organization import Organization  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.document import Document  # noqa: E402
from app.models.clause import ProcessedClause, RawClause  # noqa: E402
from app.models.playbook import OrgPlaybook  # noqa: E402
from app.models.onboarding import (  # noqa: E402
    TextbookContent,
    QuizSet,
    ContractChecklist,
)

FIXTURE_DIR = Path(__file__).parent.parent / "tests" / "fixtures"
DEMO_ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
DEMO_ADMIN_ID = uuid.UUID("00000000-0000-0000-0000-000000000010")
DEMO_HIRE_ID = uuid.UUID("00000000-0000-0000-0000-000000000011")
DEMO_ORG_NAME = "Ironbridge Engineering Ltd."


def _now():
    return datetime.now(timezone.utc)


def _seed_org(db) -> Organization:
    org = db.query(Organization).filter(Organization.id == DEMO_ORG_ID).first()
    if org:
        print("  Org already exists — skipping")
        return org
    org = Organization(
        id=DEMO_ORG_ID,
        name=DEMO_ORG_NAME,
        industry="Engineering",
        size="medium",
        plan="pro",
    )
    db.add(org)
    db.commit()
    print(f"  Created org: {DEMO_ORG_NAME}")
    return org


def _seed_users(db) -> None:
    for uid, email, role in [
        (DEMO_ADMIN_ID, "admin@ironbridge.example.com", "admin"),
        (DEMO_HIRE_ID, "newhire@ironbridge.example.com", "new_hire"),
    ]:
        if db.query(User).filter(User.id == uid).first():
            print(f"  User {email} exists — skipping")
            continue
        db.add(User(id=uid, email=email, role=role, org_id=DEMO_ORG_ID))
    db.commit()
    print("  Users seeded")


def _seed_documents(db) -> list[Document]:
    docs = []
    for i, name in enumerate(["Master_Services_Agreement_v3.pdf", "Supplier_Framework_2024.pdf"], 1):
        doc_id = uuid.UUID(f"00000000-0000-0000-0001-{i:012d}")
        existing = db.query(Document).filter(Document.id == doc_id).first()
        if existing:
            docs.append(existing)
            continue
        doc = Document(
            id=doc_id,
            org_id=DEMO_ORG_ID,
            filename=name,
            doc_type="Master Agreement",
            status="complete",
            upload_date=_now(),
            page_count=12,
            is_deleted=False,
        )
        db.add(doc)
        docs.append(doc)
    db.commit()
    print(f"  {len(docs)} documents seeded")
    return docs


def _seed_clauses(db, docs: list[Document]) -> list[ProcessedClause]:
    clause_texts = [
        {
            "clause_type": "indemnification",
            "text": "Each party shall indemnify, defend, and hold harmless the other party from and against any claims arising from the indemnifying party's breach, negligence, or willful misconduct. Maximum aggregate indemnification liability shall not exceed the total fees paid in the preceding 12 months.",
        },
        {
            "clause_type": "limitation_of_liability",
            "text": "Neither party shall be liable for indirect, incidental, consequential, punitive, or special damages. Total aggregate liability of either party shall not exceed the fees paid by Client in the twelve (12) months preceding the claim giving rise to liability.",
        },
        {
            "clause_type": "governing_law",
            "text": "This Agreement shall be governed by the laws of the State of New York. Any disputes shall be resolved exclusively in the courts of New York County, New York. Each party consents to personal jurisdiction in such courts.",
        },
        {
            "clause_type": "termination",
            "text": "Either party may terminate this Agreement for cause on 30 days written notice if the other party materially breaches and fails to cure within the notice period. Either party may terminate for convenience on 60 days notice. Sections on confidentiality, IP, indemnification, and limitation of liability survive termination.",
        },
        {
            "clause_type": "intellectual_property",
            "text": "Client shall own all deliverables specifically created for Client upon full payment (Foreground IP). Ironbridge retains all rights in its pre-existing tools, methodologies, and frameworks (Background IP). Client receives a perpetual, non-exclusive, non-transferable license to Background IP embedded in deliverables.",
        },
        {
            "clause_type": "confidentiality",
            "text": "Each party agrees to maintain the other party's Confidential Information in strict confidence for a period of five (5) years following termination of this Agreement. Standard carve-outs apply: publicly available information, independently developed information, and legally required disclosures.",
        },
    ]

    processed = []
    for i, ct in enumerate(clause_texts):
        rc_id = uuid.UUID(f"00000000-0000-0000-0002-{i:012d}")
        pc_id = uuid.UUID(f"00000000-0000-0000-0003-{i:012d}")

        if not db.query(RawClause).filter(RawClause.id == rc_id).first():
            doc = docs[i % len(docs)]
            raw = RawClause(
                id=rc_id,
                document_id=doc.id,
                org_id=DEMO_ORG_ID,
                raw_text=ct["text"],
                section_path=[ct["clause_type"].replace("_", " ").title()],
                page_number=i + 1,
                char_offset=0,
            )
            db.add(raw)

        if not db.query(ProcessedClause).filter(ProcessedClause.id == pc_id).first():
            pc = ProcessedClause(
                id=pc_id,
                raw_clause_id=rc_id,
                org_id=DEMO_ORG_ID,
                document_id=docs[i % len(docs)].id,
                clause_type=ct["clause_type"],
                clause_type_confidence=0.95,
                raw_text=ct["text"],
                entities={},
                obligations=[],
                embedding_id=None,
            )
            db.add(pc)
            processed.append(pc)

    db.commit()
    print(f"  {len(processed)} clauses seeded")
    return processed


def _seed_playbook(db, processed_clauses: list[ProcessedClause]) -> OrgPlaybook:
    existing = (
        db.query(OrgPlaybook)
        .filter(OrgPlaybook.org_id == DEMO_ORG_ID, OrgPlaybook.is_current.is_(True))
        .first()
    )
    if existing:
        print("  Playbook exists — skipping")
        return existing

    fixture = json.loads((FIXTURE_DIR / "demo_playbook.json").read_text())
    pb_id = uuid.UUID("00000000-0000-0000-0004-000000000001")
    pb = OrgPlaybook(
        id=pb_id,
        org_id=DEMO_ORG_ID,
        version=1,
        sections=fixture["sections"],
        is_current=True,
        onboarding_ready=True,
        doc_count=2,
        generated_at=_now(),
    )
    db.add(pb)
    db.commit()
    print("  Playbook seeded")
    return pb


def _seed_textbook(db, playbook: OrgPlaybook) -> None:
    if db.query(TextbookContent).filter(TextbookContent.playbook_id == playbook.id).first():
        print("  Textbook exists — skipping")
        return

    chapters = [
        {
            "chapter_index": 0,
            "title": "Introduction to Contract Law at Ironbridge",
            "content": "## Welcome to Contract Review at Ironbridge Engineering\n\nAs an engineer at Ironbridge, you will regularly encounter contracts with clients, suppliers, and partners. Understanding how we approach these documents is essential to protecting the firm and delivering projects successfully.\n\nContracts are not just legal formalities — they define the rules of engagement for every project. A poorly negotiated contract can expose Ironbridge to uncapped liability, loss of intellectual property, or disputes in unfavorable jurisdictions.\n\n## What You Need to Know\n\nThis textbook walks you through the key clause types that appear in Ironbridge's contracts, our standard positions on each, and the red flags you should escalate to legal counsel immediately.",
            "key_takeaways": [
                "Contracts define the rules of every project engagement",
                "Ironbridge has standard positions on all major clause types",
                "When in doubt, escalate to legal — never sign without review"
            ],
            "clause_types": []
        },
        {
            "chapter_index": 1,
            "title": "Indemnification and Risk Allocation",
            "content": "## Indemnification at Ironbridge\n\nIndemnification clauses determine who bears the cost when something goes wrong. Ironbridge's position is always **mutual indemnification** — both parties protect each other from losses caused by their own breach or negligence.\n\n## What to Watch For\n\n**Non-negotiables:** We never accept unilateral indemnification in the counterparty's favor. If a contract requires Ironbridge to indemnify the client but not vice versa, this must be escalated.\n\n**Liability caps:** Indemnification should always be subject to the overall liability cap. Uncapped indemnification is a deal-breaker.\n\n## Standard Language\n\nOur preferred language: *'Each party shall indemnify and hold harmless the other from claims arising from its own breach, negligence, or willful misconduct.'*",
            "key_takeaways": [
                "Mutual indemnification is non-negotiable — never accept one-sided exposure",
                "Indemnification must be capped at the overall liability cap",
                "IP indemnification from vendors protecting us from infringement claims is always required"
            ],
            "clause_types": ["indemnification"]
        },
        {
            "chapter_index": 2,
            "title": "Limitation of Liability",
            "content": "## Why Liability Caps Matter\n\nWithout a liability cap, a single project failure could expose Ironbridge to claims worth multiples of the contract value. Every contract must have a mutual cap.\n\n## Our Position\n\nIronbridge's standard position is a cap at **100% of fees paid in the preceding 12 months**. For high-risk engagements, we may negotiate up to 200%.\n\n## Consequential Damages\n\nWe always insist on a mutual exclusion of consequential, indirect, punitive, and special damages. This protects Ironbridge from claims like lost profits or business interruption that would be disproportionate to the fees received.",
            "key_takeaways": [
                "Every contract must have a mutual liability cap — typically 12 months of fees",
                "Consequential and indirect damages must be mutually excluded",
                "Asymmetric caps (our exposure higher than counterparty's) are red flags"
            ],
            "clause_types": ["limitation_of_liability"]
        },
        {
            "chapter_index": 3,
            "title": "Governing Law, IP, Confidentiality & Termination",
            "content": "## Governing Law\n\nIronbridge prefers **New York law** with exclusive jurisdiction in New York County. We accept Delaware, Ontario, and England & Wales for counterparties based in those jurisdictions.\n\n## Intellectual Property\n\nThis is critical: Ironbridge retains all **background IP** (our methodologies, tools, frameworks). Clients own the **foreground IP** (deliverables created specifically for them) upon full payment. Background IP embedded in deliverables is licensed, not assigned.\n\n## Confidentiality\n\nMutual, 5-year post-termination. Perpetual for trade secrets.\n\n## Termination\n\n30-day cure period before termination for cause. 60-day notice for convenience. Payment for all work completed upon termination regardless of which party terminates.",
            "key_takeaways": [
                "New York law preferred — escalate any civil law jurisdiction proposals",
                "Background IP (methodologies) is never assigned — only licensed",
                "Confidentiality obligations run 5 years post-termination"
            ],
            "clause_types": ["governing_law", "intellectual_property", "confidentiality", "termination"]
        },
        {
            "chapter_index": 4,
            "title": "Red Flags and When to Escalate",
            "content": "## When to Stop and Call Legal\n\nNot every contract issue requires escalation, but some absolutely do. If you see any of the following, stop the negotiation and contact the legal team immediately.\n\n**Always escalate:**\n- Unilateral indemnification (vendor only protects client)\n- Uncapped liability for any category\n- IP assignment of background/pre-existing IP\n- Governing law in a jurisdiction with limited enforcement\n- Termination for convenience with less than 30 days notice on long engagements\n- Confidentiality terms under 2 years\n\n## The Golden Rule\n\nIf you are unsure whether something is acceptable, assume it is not and ask. The cost of a legal review is always less than the cost of a bad contract.",
            "key_takeaways": [
                "Unilateral indemnification, uncapped liability, and IP assignment are immediate escalation triggers",
                "When in doubt, escalate — the cost of review is always less than the cost of a bad contract",
                "Red flags compound: two borderline clauses together may be worse than one clearly bad clause"
            ],
            "clause_types": []
        }
    ]

    tb = TextbookContent(
        id=uuid.UUID("00000000-0000-0000-0005-000000000001"),
        playbook_id=playbook.id,
        org_id=DEMO_ORG_ID,
        chapters=chapters,
        page_estimate=14,
        generated_at=_now(),
    )
    db.add(tb)
    db.commit()
    print("  Textbook seeded")


def _seed_quizzes(db, playbook: OrgPlaybook) -> None:
    if db.query(QuizSet).filter(QuizSet.playbook_id == playbook.id).first():
        print("  Quizzes exist — skipping")
        return

    chapter_quiz = {
        "quiz_type": "chapter_mcq",
        "chapter_index": 1,
        "questions": [
            {
                "question": "What is Ironbridge's minimum acceptable indemnification structure?",
                "options": ["Unilateral (client protected only)", "Mutual indemnification", "No indemnification clause", "Indemnification capped at $1M"],
                "correct_answer": "Mutual indemnification",
                "explanation": "Ironbridge never accepts unilateral indemnification. Both parties must protect each other from losses caused by their own breach or negligence."
            },
            {
                "question": "What is Ironbridge's standard liability cap?",
                "options": ["100% of fees paid in preceding 12 months", "200% of total contract value", "$5 million fixed cap", "Unlimited liability"],
                "correct_answer": "100% of fees paid in preceding 12 months",
                "explanation": "Ironbridge's standard position caps total liability at 100% of fees paid in the 12 months preceding the claim."
            },
            {
                "question": "True or False: Ironbridge assigns background IP (methodologies and tools) to clients as part of standard deliverables.",
                "options": ["True", "False"],
                "correct_answer": "False",
                "explanation": "Background IP is never assigned. Clients receive a limited, non-exclusive license to use background IP embedded in their deliverables."
            },
            {
                "question": "Which of the following is an immediate escalation trigger?",
                "options": ["Counterparty requests 30-day cure period", "Unilateral indemnification in client's favor only", "Client requests New York governing law", "60-day termination notice for convenience"],
                "correct_answer": "Unilateral indemnification in client's favor only",
                "explanation": "Unilateral indemnification where only Ironbridge provides protection is a non-negotiable red flag requiring immediate escalation to legal."
            }
        ]
    }

    final_quiz = {
        "quiz_type": "final_assessment",
        "chapter_index": None,
        "questions": [
            {
                "question": "Ironbridge's preferred governing law jurisdiction is:",
                "options": ["California", "New York", "Texas", "Federal law"],
                "correct_answer": "New York",
                "explanation": "Ironbridge prefers New York law as it has the most developed commercial contract law among common law jurisdictions."
            },
            {
                "question": "What is the minimum post-termination confidentiality period Ironbridge accepts?",
                "options": ["1 year", "2 years", "3 years", "5 years"],
                "correct_answer": "3 years",
                "explanation": "Ironbridge requires a minimum 3-year post-termination confidentiality obligation, with 5 years as the standard position."
            },
            {
                "question": "True or False: Consequential damages exclusions in our contracts are one-sided (protecting only Ironbridge).",
                "options": ["True", "False"],
                "correct_answer": "False",
                "explanation": "Consequential damages exclusions must be mutual — both parties waive consequential damages claims against each other."
            },
            {
                "question": "Upon termination for convenience, the client's payment obligation is:",
                "options": ["Nothing — termination cancels all fees", "Only fees for deliverables fully accepted", "All fees for services rendered through termination date", "A penalty equal to 50% of remaining contract value"],
                "correct_answer": "All fees for services rendered through termination date",
                "explanation": "Ironbridge always requires payment for all work completed up to the termination date, regardless of which party terminates."
            }
        ]
    }

    for i, quiz_data in enumerate([chapter_quiz, final_quiz]):
        db.add(QuizSet(
            id=uuid.UUID(f"00000000-0000-0000-0006-{i:012d}"),
            playbook_id=playbook.id,
            org_id=DEMO_ORG_ID,
            quiz_type=quiz_data["quiz_type"],
            chapter_index=quiz_data["chapter_index"],
            questions=quiz_data["questions"],
            generated_at=_now(),
        ))
    db.commit()
    print("  Quizzes seeded")


def _seed_checklist(db, playbook: OrgPlaybook) -> None:
    if db.query(ContractChecklist).filter(ContractChecklist.playbook_id == playbook.id).first():
        print("  Checklist exists — skipping")
        return

    categories = [
        {
            "category": "Indemnification",
            "items": [
                {"item": "Mutual indemnification structure confirmed", "is_mandatory": True, "why_it_matters": "Unilateral exposure creates unlimited downside for Ironbridge"},
                {"item": "Indemnification subject to liability cap", "is_mandatory": True, "why_it_matters": "Uncapped indemnification is a deal-breaker"},
                {"item": "IP infringement indemnification from vendor included", "is_mandatory": False, "why_it_matters": "Protects Ironbridge from third-party IP claims arising from vendor's tools"},
                {"item": "Gross negligence carve-out present", "is_mandatory": False, "why_it_matters": "Prevents indemnified party from claiming indemnity for its own gross misconduct"}
            ]
        },
        {
            "category": "Limitation of Liability",
            "items": [
                {"item": "Mutual liability cap present", "is_mandatory": True, "why_it_matters": "Without a cap, one bad project could expose Ironbridge to catastrophic loss"},
                {"item": "Cap expressed as fee multiple (min 12 months)", "is_mandatory": True, "why_it_matters": "Fixed dollar caps may be insufficient; fee-based caps are proportionate"},
                {"item": "Consequential damages mutually excluded", "is_mandatory": True, "why_it_matters": "Lost profits and business interruption claims would far exceed contract value"},
                {"item": "Cap is symmetrical between parties", "is_mandatory": False, "why_it_matters": "Asymmetric caps indicate unequal negotiating leverage — escalate for review"}
            ]
        },
        {
            "category": "Intellectual Property",
            "items": [
                {"item": "Background IP retained by Ironbridge", "is_mandatory": True, "why_it_matters": "Background IP is core to our business — assignment would be irreversible harm"},
                {"item": "Foreground IP vests on full payment", "is_mandatory": True, "why_it_matters": "Prevents IP transfer before Ironbridge is paid"},
                {"item": "Background IP license is non-exclusive and non-transferable", "is_mandatory": True, "why_it_matters": "Broad license could allow client to compete with Ironbridge"},
                {"item": "No work-for-hire provisions covering background IP", "is_mandatory": True, "why_it_matters": "Work-for-hire automatically assigns all IP — must be explicitly excluded"}
            ]
        },
        {
            "category": "Governing Law & Dispute Resolution",
            "items": [
                {"item": "Common law jurisdiction confirmed", "is_mandatory": True, "why_it_matters": "Civil law jurisdictions have materially different enforcement mechanisms"},
                {"item": "Exclusive jurisdiction clause is mutual", "is_mandatory": False, "why_it_matters": "Unilateral venue selection forces Ironbridge to litigate in counterparty's home court"},
                {"item": "Arbitration clause includes carve-out for injunctive relief", "is_mandatory": False, "why_it_matters": "Without this carve-out, Ironbridge cannot seek emergency injunctions in court"}
            ]
        },
        {
            "category": "Termination",
            "items": [
                {"item": "30-day cure period before termination for cause", "is_mandatory": True, "why_it_matters": "Ironbridge needs time to remedy any alleged breach before losing the contract"},
                {"item": "Payment for all completed work upon termination", "is_mandatory": True, "why_it_matters": "Ironbridge must be compensated for value delivered regardless of who terminates"},
                {"item": "Survival clause covers all key provisions", "is_mandatory": True, "why_it_matters": "Key obligations must survive contract end — especially confidentiality and IP"},
                {"item": "Termination for convenience notice period ≥ 30 days", "is_mandatory": False, "why_it_matters": "Short notice periods leave insufficient time for wind-down and transition"}
            ]
        }
    ]

    db.add(ContractChecklist(
        id=uuid.UUID("00000000-0000-0000-0007-000000000001"),
        playbook_id=playbook.id,
        org_id=DEMO_ORG_ID,
        categories=categories,
        generated_at=_now(),
    ))
    db.commit()
    print("  Checklist seeded")


def _seed_qdrant(processed_clauses_texts: list[dict]) -> None:
    try:
        from app.services.retrieval.embedder import EmbeddingService, COLLECTION_NAME
        EmbeddingService.ensure_collection_exists()
        model = EmbeddingService.get_model()
        texts = [c["text"] for c in processed_clauses_texts]
        embeddings = model.encode(texts, show_progress_bar=False)
        from qdrant_client.models import PointStruct
        client = EmbeddingService.get_qdrant()
        points = [
            PointStruct(
                id=str(uuid.UUID(f"00000000-0000-0000-0003-{i:012d}")),
                vector=emb.tolist(),
                payload={
                    "org_id": str(DEMO_ORG_ID),
                    "clause_db_id": str(uuid.UUID(f"00000000-0000-0000-0003-{i:012d}")),
                    "clause_type": c["clause_type"],
                },
            )
            for i, (c, emb) in enumerate(zip(processed_clauses_texts, embeddings))
        ]
        client.upsert(collection_name=COLLECTION_NAME, points=points)
        print(f"  {len(points)} clause embeddings upserted to Qdrant")
    except Exception as exc:
        print(f"  WARNING: Qdrant seed failed ({exc}) — chat RAG will not work until Qdrant is running")


CLAUSE_TEXTS_FOR_QDRANT = [
    {"clause_type": "indemnification", "text": "Each party shall indemnify, defend, and hold harmless the other party from and against any claims arising from the indemnifying party's breach, negligence, or willful misconduct. Maximum aggregate indemnification liability shall not exceed the total fees paid in the preceding 12 months."},
    {"clause_type": "limitation_of_liability", "text": "Neither party shall be liable for indirect, incidental, consequential, punitive, or special damages. Total aggregate liability of either party shall not exceed the fees paid by Client in the twelve (12) months preceding the claim giving rise to liability."},
    {"clause_type": "governing_law", "text": "This Agreement shall be governed by the laws of the State of New York. Any disputes shall be resolved exclusively in the courts of New York County, New York. Each party consents to personal jurisdiction in such courts."},
    {"clause_type": "termination", "text": "Either party may terminate this Agreement for cause on 30 days written notice if the other party materially breaches and fails to cure within the notice period. Either party may terminate for convenience on 60 days notice."},
    {"clause_type": "intellectual_property", "text": "Client shall own all deliverables specifically created for Client upon full payment. Ironbridge retains all rights in its pre-existing tools, methodologies, and frameworks. Client receives a perpetual, non-exclusive, non-transferable license to background IP embedded in deliverables."},
    {"clause_type": "confidentiality", "text": "Each party agrees to maintain the other party's Confidential Information in strict confidence for a period of five (5) years following termination. Standard carve-outs apply for publicly available information, independently developed information, and legally required disclosures."},
]


def main():
    print("=== LexOnboard Demo Seed ===")
    print(f"Target DB: {settings.DATABASE_URL}")

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("\n[1/7] Seeding org...")
        _seed_org(db)

        print("[2/7] Seeding users...")
        _seed_users(db)

        print("[3/7] Seeding documents...")
        docs = _seed_documents(db)

        print("[4/7] Seeding clauses...")
        _seed_clauses(db, docs)

        print("[5/7] Seeding playbook...")
        playbook = _seed_playbook(db, [])

        print("[6/7] Seeding onboarding content...")
        _seed_textbook(db, playbook)
        _seed_quizzes(db, playbook)
        _seed_checklist(db, playbook)

    finally:
        db.close()

    print("[7/7] Seeding Qdrant embeddings...")
    _seed_qdrant(CLAUSE_TEXTS_FOR_QDRANT)

    print("\n=== Done ===")
    print(f"Org:      {DEMO_ORG_NAME}")
    print(f"Org ID:   {DEMO_ORG_ID}")
    print(f"Admin ID: {DEMO_ADMIN_ID}")
    print(f"Hire ID:  {DEMO_HIRE_ID}")
    print("\nSet in .env.local:")
    print(f"  NEXT_PUBLIC_DEV_ORG_ID={DEMO_ORG_ID}")
    print(f"  NEXT_PUBLIC_DEV_USER_ID={DEMO_ADMIN_ID}   # or {DEMO_HIRE_ID} for new_hire view")


if __name__ == "__main__":
    main()
