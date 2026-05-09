from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func, text

from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    org_id = Column(UUID(as_uuid=True), nullable=False)
    filename = Column(String, nullable=False)
    doc_type = Column(String, nullable=False)  # master_agreement|compliance|nda|sow|other
    storage_path = Column(String, nullable=False)
    upload_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(String, nullable=False, default="pending")
    # pending|ingesting|nlp_processing|distilling|complete|error
    job_id = Column(String, nullable=True)
    page_count = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    metadata_ = Column(JSONB, nullable=True, default={})
    is_deleted = Column(Boolean, nullable=False, default=False)

    __table_args__ = (Index("ix_documents_org_id", "org_id"),)