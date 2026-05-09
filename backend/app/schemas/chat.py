from pydantic import BaseModel, field_validator


class ChatQueryRequest(BaseModel):
    question: str
    session_id: str
    conversation_history: list[dict]

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("question must not be empty")
        return v


class SourceClause(BaseModel):
    id: str
    clause_type: str
    section_path: list[str]
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceClause]
    session_id: str