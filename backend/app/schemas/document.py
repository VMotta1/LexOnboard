from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DocumentUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    doc_type: str
    status: str
    job_id: Optional[str] = None


class DocumentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    doc_type: str
    status: str
    upload_date: datetime
    page_count: Optional[int] = None


class PipelineStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    stage: str
    progress_pct: int
    error: Optional[str] = None
    document_id: Optional[str] = None