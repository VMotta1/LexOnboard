from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TextbookChapterSchema(BaseModel):
    title: str
    chapter_number: int
    content: str
    key_takeaways: list[str]


class TextbookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    chapters: list[TextbookChapterSchema]
    page_estimate: int
    generated_at: datetime


class QuestionSchema(BaseModel):
    id: str
    question_type: str  # mcq|true_false|scenario
    text: str
    context: Optional[str] = None
    options: Optional[list[str]] = None
    correct_answer: str
    explanation: str
    clause_type: str


class QuizSetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    quiz_type: str
    questions: list[QuestionSchema]


class ChecklistItemSchema(BaseModel):
    item_clause: str
    review_question: str
    is_non_negotiable: bool
    clause_type: str


class ChecklistSubcategorySchema(BaseModel):
    name: str
    items: list[ChecklistItemSchema]


class ChecklistCategorySchema(BaseModel):
    name: str
    subcategories: list[ChecklistSubcategorySchema]


class ContractChecklistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    categories: list[ChecklistCategorySchema]


class QuizScoreUpdate(BaseModel):
    quiz_id: str
    score: float


class OnboardingProgressUpdate(BaseModel):
    chapters_read: Optional[list[int]] = None
    quiz_score: Optional[QuizScoreUpdate] = None


class OnboardingProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chapters_read: list[int]
    quizzes_completed: list[str]
    quiz_scores: dict[str, float]
    checklist_uses: int
    chat_queries: int
    completion_percentage: float