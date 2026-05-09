import logging
import time
import uuid

from app.api.cache import cache_delete_pattern, playbook_cache_key
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.onboarding import ContractChecklist, OnboardingProgress, QuizSet, TextbookContent
from app.models.organization import Organization
from app.models.playbook import OrgPlaybook

logger = logging.getLogger(__name__)


def _generate_onboarding_impl(org_id: str, playbook_id: str) -> None:
    db = SessionLocal()
    try:
        playbook = db.query(OrgPlaybook).filter(OrgPlaybook.id == uuid.UUID(playbook_id)).first()
        if not playbook:
            logger.error(f"generate_onboarding: playbook {playbook_id} not found")
            return

        org = db.query(Organization).filter(Organization.id == uuid.UUID(org_id)).first()
        org_name = org.name if org else "Your Organization"

        sections = playbook.sections or []

        # ── Clear stale onboarding content for this playbook ─────────────────
        db.query(QuizSet).filter(QuizSet.playbook_id == uuid.UUID(playbook_id)).delete()
        db.query(ContractChecklist).filter(ContractChecklist.playbook_id == uuid.UUID(playbook_id)).delete()
        db.query(TextbookContent).filter(TextbookContent.playbook_id == uuid.UUID(playbook_id)).delete()
        db.commit()

        # ── Textbook ─────────────────────────────────────────────────────────
        from app.services.generation.textbook import generate_textbook

        textbook_data = generate_textbook(playbook, org_name=org_name)
        chapters = textbook_data["chapters"]

        textbook_record = TextbookContent(
            id=uuid.uuid4(),
            org_id=uuid.UUID(org_id),
            playbook_id=uuid.UUID(playbook_id),
            page_estimate=textbook_data["page_estimate"],
            chapters=chapters,
        )
        db.add(textbook_record)
        db.commit()
        logger.info(
            f"Textbook generated: {len(chapters)} chapters, "
            f"~{textbook_data['page_estimate']} pages"
        )

        # ── Chapter Quizzes ───────────────────────────────────────────────────
        from app.services.generation.quiz import generate_final_assessment, generate_quiz_for_chapter

        section_by_type = {s.get("clause_type"): s for s in sections}

        chapter_quizzes: list[dict] = []
        for i, chapter in enumerate(chapters):
            clause_type = chapter.get("clause_type")
            if clause_type is None:
                continue
            if i > 0:
                time.sleep(20)

            section = section_by_type.get(clause_type, {"clause_type": clause_type})
            quiz_data = generate_quiz_for_chapter(chapter, section)

            quiz_record = QuizSet(
                id=uuid.UUID(quiz_data["id"]),
                org_id=uuid.UUID(org_id),
                playbook_id=uuid.UUID(playbook_id),
                chapter_index=quiz_data.get("chapter_index"),
                quiz_type=quiz_data["quiz_type"],
                questions=quiz_data["questions"],
            )
            db.add(quiz_record)
            chapter_quizzes.append(quiz_data)

        db.commit()
        logger.info(f"{len(chapter_quizzes)} chapter quiz sets generated")

        # ── Final Assessment ──────────────────────────────────────────────────
        if chapter_quizzes:
            final_data = generate_final_assessment(chapter_quizzes, sections)
            final_record = QuizSet(
                id=uuid.UUID(final_data["id"]),
                org_id=uuid.UUID(org_id),
                playbook_id=uuid.UUID(playbook_id),
                chapter_index=None,
                quiz_type="final_assessment",
                questions=final_data["questions"],
            )
            db.add(final_record)
            db.commit()
            logger.info(
                f"Final assessment generated: {len(final_data['questions'])} questions"
            )

        # ── Checklist ─────────────────────────────────────────────────────────
        from app.services.generation.checklist import generate_checklist

        checklist_data = generate_checklist(playbook)
        checklist_record = ContractChecklist(
            id=uuid.uuid4(),
            org_id=uuid.UUID(org_id),
            playbook_id=uuid.UUID(playbook_id),
            categories=checklist_data["categories"],
        )
        db.add(checklist_record)
        db.commit()
        logger.info(
            f"Checklist generated: {len(checklist_data['categories'])} categories"
        )

        # ── Mark playbook ready ────────────────────────────────────────────────
        playbook.onboarding_ready = True
        db.commit()

        # Bust cache so next GET returns onboarding_ready=true
        cache_delete_pattern(playbook_cache_key(org_id))

        logger.info(f"Onboarding content generation complete for org {org_id}")

    except Exception as exc:
        logger.error(
            f"generate_onboarding failed for org {org_id} playbook {playbook_id}: {exc}",
            exc_info=True,
        )
        raise
    finally:
        db.close()


@celery_app.task
def generate_onboarding(org_id: str, playbook_id: str):
    """
    Generate textbook, quizzes, and checklist from the current OrgPlaybook.
    Triggered automatically after regenerate_playbook completes.
    """
    _generate_onboarding_impl(org_id, playbook_id)
