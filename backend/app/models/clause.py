from sqlalchemy import Column, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import text

from app.database import Base


class RawClause(Base):
    __tablename__ = "raw_clauses"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    org_id = Column(UUID(as_uuid=True), nullable=False)
    text = Column(Text, nullable=False)
    section_path = Column(JSONB, nullable=False, default=[])
    page_number = Column(Integer, nullable=False, default=0)
    char_offset = Column(Integer, nullable=False, default=0)

    __table_args__ = (Index("ix_raw_clauses_org_id", "org_id"),)


class ProcessedClause(Base):
    __tablename__ = "processed_clauses"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    raw_clause_id = Column(
        UUID(as_uuid=True),
        ForeignKey("raw_clauses.id", ondelete="CASCADE"),
        nullable=False,
    )
    org_id = Column(UUID(as_uuid=True), nullable=False)
    clause_type = Column(String, nullable=False)
    clause_type_confidence = Column(Float, nullable=False, default=0.0)
    entities = Column(JSONB, nullable=False, default={})
    obligations = Column(JSONB, nullable=False, default=[])
    embedding_id = Column(String, nullable=True)
    raw_text = Column(Text, nullable=False)

    __table_args__ = (Index("ix_processed_clauses_org_id", "org_id"),)