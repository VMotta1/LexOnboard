from sqlalchemy import Column, DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, text

from app.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name = Column(String, nullable=False)
    industry = Column(String, nullable=False)  # engineering|legal|real_estate|tech|other
    size = Column(String, nullable=False)  # small|medium
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    plan = Column(String, nullable=False, default="trial")  # trial|pro