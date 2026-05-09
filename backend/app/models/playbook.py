from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func, text

from app.database import Base


class OrgPlaybook(Base):
    __tablename__ = "org_playbooks"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    org_id = Column(UUID(as_uuid=True), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_current = Column(Boolean, nullable=False, default=False)
    sections = Column(JSONB, nullable=False, default=[])
    onboarding_ready = Column(Boolean, nullable=False, default=False)
    doc_count = Column(Integer, nullable=False, default=0)

    __table_args__ = (Index("ix_org_playbooks_org_id", "org_id"),)


class PlaybookEdit(Base):
    __tablename__ = "playbook_edits"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    playbook_id = Column(
        UUID(as_uuid=True),
        ForeignKey("org_playbooks.id", ondelete="CASCADE"),
        nullable=False,
    )
    clause_type = Column(String, nullable=False)
    edited_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    edit_data = Column(JSONB, nullable=False, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    approved = Column(Boolean, nullable=False, default=False)