from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class StandardPosition(BaseModel):
    description: str
    acceptable_range: str
    rationale: str


class PlaybookSectionSchema(BaseModel):
    clause_type: str
    title: str
    non_negotiables: list[str]
    standard_positions: list[StandardPosition]
    red_flags: list[str]
    industry_baseline: str
    example_clauses: list[str]
    source_doc_ids: list[str]


class OrgPlaybookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    version: int
    generated_at: datetime
    is_current: bool
    sections: list[PlaybookSectionSchema]
    onboarding_ready: bool
    doc_count: int


class ExportRequest(BaseModel):
    format: str  # docx|pdf


class ExportResponse(BaseModel):
    download_url: str
    expires_at: datetime