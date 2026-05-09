from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    # Primary key matches Supabase Auth UUID — provided externally, no server_default
    id = Column(UUID(as_uuid=True), primary_key=True)
    org_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    email = Column(String, nullable=False)
    role = Column(String, nullable=False)  # admin|lawyer|new_hire|reviewer
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_active = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ix_users_org_id", "org_id"),)