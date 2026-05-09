export interface Document {
  id: string;
  filename: string;
  doc_type: string;
  status: "pending" | "nlp_processing" | "distilling" | "complete" | "error";
  upload_date: string;
  is_deleted: boolean;
  metadata: Record<string, unknown>;
}

export interface DocumentListItem {
  id: string;
  filename: string;
  doc_type: string;
  status: string;
  upload_date: string;
  page_count?: number | null;
}

export interface PipelineStatus {
  job_id: string;
  stage: string;
  progress_pct: number;
  error?: string;
  document_id?: string | null;
}

export interface StandardPosition {
  title?: string;
  our_position?: string;
  description?: string;
  acceptable_variations?: string[];
  acceptable_range?: string;
  rationale?: string;
}

export interface PlaybookSection {
  clause_type: string;
  non_negotiables: string[];
  standard_positions: StandardPosition[];
  red_flags: string[];
  industry_baseline: string;
  version: number;
  last_edited_at: string | null;
}

export interface OrgPlaybook {
  id: string;
  org_id: string;
  version: number;
  sections: PlaybookSection[];
  is_current: boolean;
  onboarding_ready: boolean;
  created_at: string;
}

export interface TextbookChapter {
  chapter_index: number;
  title: string;
  content: string;
  key_takeaways: string[];
  clause_types: string[];
}

export interface TextbookContent {
  id: string;
  chapters: TextbookChapter[];
  page_estimate: number;
  generated_at: string;
}

export interface Question {
  id?: string;
  question_type?: string;
  text: string;
  context?: string | null;
  options: string[];
  correct_answer: string;
  explanation: string;
  clause_type?: string;
}

export interface QuizSet {
  id: string;
  quiz_type: string;
  questions: Question[];
}

export interface ChecklistItem {
  item: string;
  is_mandatory: boolean;
  why_it_matters?: string;
  risk_level?: "high" | "medium" | "low";
  contract_value?: string;
}

export interface ChecklistCategory {
  category: string;
  items: ChecklistItem[];
}

export interface ContractChecklist {
  id: string;
  categories: ChecklistCategory[];
}

export interface OnboardingProgress {
  chapters_read: number[];
  quizzes_completed: string[];
  quiz_scores: Record<string, number>;
  checklist_uses: number;
  chat_queries: number;
  completion_percentage: number;
}

export interface SourceClause {
  id: string;
  clause_type: string;
  section_path: string[];
  excerpt: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  source_clause_ids: string[];
  created_at: string | null;
}

export interface ChatResponse {
  answer: string;
  sources: SourceClause[];
  session_id: string;
}
