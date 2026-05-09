from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func, text

from app.database import Base


class TextbookContent(Base):
    __tablename__ = "textbook_contents"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    org_id = Column(UUID(as_uuid=True), nullable=False)
    playbook_id = Column(
        UUID(as_uuid=True),
        ForeignKey("org_playbooks.id", ondelete="CASCADE"),
        nullable=False,
    )
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    page_estimate = Column(Integer, nullable=False, default=10)
    chapters = Column(JSONB, nullable=False, default=[])

    __table_args__ = (Index("ix_textbook_contents_org_id", "org_id"),)


class QuizSet(Base):
    __tablename__ = "quiz_sets"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    org_id = Column(UUID(as_uuid=True), nullable=False)
    playbook_id = Column(
        UUID(as_uuid=True),
        ForeignKey("org_playbooks.id", ondelete="CASCADE"),
        nullable=False,
    )
    chapter_index = Column(Integer, nullable=True)
    quiz_type = Column(String, nullable=False)  # chapter_review|scenario|final_assessment
    questions = Column(JSONB, nullable=False, default=[])
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (Index("ix_quiz_sets_org_id", "org_id"),)


class ContractChecklist(Base):
    __tablename__ = "contract_checklists"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    org_id = Column(UUID(as_uuid=True), nullable=False)
    playbook_id = Column(
        UUID(as_uuid=True),
        ForeignKey("org_playbooks.id", ondelete="CASCADE"),
        nullable=False,
    )
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    categories = Column(JSONB, nullable=False, default=[])

    __table_args__ = (Index("ix_contract_checklists_org_id", "org_id"),)


class OnboardingProgress(Base):
    __tablename__ = "onboarding_progress"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    org_id = Column(UUID(as_uuid=True), nullable=False)
    chapters_read = Column(JSONB, nullable=False, default=[])
    quizzes_completed = Column(JSONB, nullable=False, default=[])
    quiz_scores = Column(JSONB, nullable=False, default={})
    checklist_uses = Column(Integer, nullable=False, default=0)
    chat_queries = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_onboarding_progress_user_id"),
        Index("ix_onboarding_progress_org_id", "org_id"),
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    session_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    org_id = Column(UUID(as_uuid=True), nullable=False)
    role = Column(String, nullable=False)  # user|assistant
    content = Column(Text, nullable=False)
    source_clause_ids = Column(JSONB, nullable=False, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (Index("ix_chat_messages_org_id", "org_id"),)