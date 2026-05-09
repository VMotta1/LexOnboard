# LexOnboard — AI-Powered Legal Contract Onboarding Platform

> **LexOnboard** turns a company's contract history into structured institutional knowledge — then delivers that knowledge as an interactive onboarding layer for new hires. Upload master agreements and compliance documents; get a living playbook and a training curriculum. New hires draft like veterans. Senior lawyers stop being classrooms.

---

## Table of Contents

1. [Architecture](#1-architecture)
2. [Data Flow](#2-data-flow)
3. [Data Structures](#3-data-structures)
4. [Deliverables & Implementation Steps](#4-deliverables--implementation-steps)
5. [Technical Implementation Details](#5-technical-implementation-details)
6. [Demo Flow (5 Minutes)](#6-demo-flow-5-minutes)
7. [Success Criteria](#7-success-criteria)
8. [Future Enhancements (AI-Powered)](#8-future-enhancements-ai-powered)

---

## Should You Use NLP? Yes — Here's Why and How

Generic LLM tools fail for this use case because they can't hold an entire contract corpus in context, they hallucinate clause semantics, and they have no awareness of what's standard vs. what's a non-negotiable for a specific org. NLP solves this at the ingestion layer — before the LLM ever sees anything.

**NLP pipeline roles:**

| NLP Task | Tool | What It Does |
|----------|------|--------------|
| Document parsing | `Unstructured.io` | Extracts clean text from messy PDFs/DOCX, preserving section hierarchy |
| Named Entity Recognition | `LegalBERT` + `spaCy` | Extracts parties, dates, monetary values, jurisdictions, defined terms |
| Clause classification | CUAD-fine-tuned `RoBERTa` | Labels each clause by type: indemnity, liability cap, termination, IP ownership, etc. |
| Semantic chunking | `LangChain` splitters | Splits by clause boundary rather than token count — preserves legal meaning |
| Obligation extraction | Dependency parsing (`spaCy`) | Identifies who must do what by when: `(subject, deontic_verb, action, condition)` |
| Cross-reference resolution | Embedding similarity | Resolves "as defined in Section 3.2(b)..." using vector lookup |
| Distillation | Claude API (`claude-sonnet-4`) | Synthesizes NLP output into structured non-negotiables JSON |
| Generation | Claude API (`claude-sonnet-4`) | Produces textbook content, quizzes, checklists from the distilled JSON |

The key insight: NLP does the heavy structural lifting cheaply and deterministically; Claude does the semantic synthesis and generation. This keeps token usage low and output quality high.

---

## Auth Status

**Auth is deferred.** The current build uses `X-Org-ID` / `X-User-ID` / `X-User-Role` headers for identity. All data is already org-scoped at the DB level, so adding auth later is a drop-in replacement of the dependency in `deps.py` — nothing else changes. Supabase Auth + storage will be added in a later phase.

---

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS v4, shadcn/ui | Matches GoCerise stack; SSR for SEO, fast iteration |
| **Backend API** | FastAPI (Python 3.11+) | Matches prior internships; async-native, great for long-running pipelines |
| **LLM** | Anthropic Claude API (`claude-sonnet-4-20250514`) | Best legal reasoning, 200k context window for large contracts |
| **NLP** | spaCy, `en-core-web-trf`, LegalBERT (HuggingFace) | Domain-specific legal NER; CUAD classifier for clause typing |
| **Orchestration** | LangChain | Chains ingestion → NLP → distillation → generation |
| **Vector DB** | Qdrant (self-hosted or cloud) | Open-source, fast, great Python SDK, embeds well with LangChain |
| **Embeddings** | `text-embedding-3-small` (OpenAI) or `BAAI/bge-m3` | Dense retrieval for RAG layer |
| **Database** | PostgreSQL via Supabase | Structured org/user/document data; Row-Level Security for multi-tenancy |
| **File Storage** | Supabase Storage | Stores raw uploads (PDF, DOCX) |
| **Auth** | Supabase Auth | Email/password + magic link; org-level isolation via RLS |
| **Task Queue** | Celery + Redis | Async document processing (ingestion pipeline is slow — don't block the UI) |
| **Export** | `python-docx`, `fpdf2` | Generate Word + PDF outputs |
| **Deployment** | Vercel (frontend) + Railway (backend + Redis + Qdrant) | Fast iteration, generous free tiers |

---

## 1. Architecture

### Pattern: Pipeline-Oriented Service Architecture + RAG

**Why this pattern**: Legal document processing is fundamentally a pipeline problem, not a CRUD problem. Data flows in one direction — ingest → process → distill → serve — with the distilled artifact as the central state. The RAG layer sits on top of that artifact to power the interactive query interface.

### Layer Breakdown

| Layer | Role | Technology |
|-------|------|------------|
| **Ingestion Service** | Parse raw documents (PDF, DOCX, TXT) into clean structured text | Unstructured.io, python-docx, PyMuPDF |
| **NLP Service** | Classify clauses, extract entities, chunk semantically | spaCy, LegalBERT, CUAD-RoBERTa, LangChain |
| **Distillation Service** | Synthesize NLP output into structured org playbook via LLM | Claude API, LangChain |
| **Knowledge Base** | Store distilled clauses + embeddings for retrieval | PostgreSQL (Supabase) + Qdrant |
| **Generation Service** | Produce textbook, quizzes, checklists, contract checklist | Claude API |
| **API Gateway** | FastAPI REST endpoints; async task management | FastAPI, Celery, Redis |
| **Frontend** | Upload UI, progress tracking, viewer, interactive training layer | Next.js, React, Tailwind |

### Project Structure

```
lexonboard/
├── backend/
│   ├── app/
│   │   ├── main.py                          ← FastAPI entry point, router registration
│   │   ├── config.py                        ← Env vars, settings (Pydantic BaseSettings)
│   │   ├── database.py                      ← Supabase client, SQLAlchemy session
│   │   ├── celery_app.py                    ← Celery config + Redis broker
│   │   │
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── documents.py             ← Upload, list, delete documents
│   │   │   │   ├── pipeline.py              ← Trigger processing, check job status
│   │   │   │   ├── playbook.py              ← Get/update org playbook
│   │   │   │   ├── onboarding.py            ← Get textbook, quizzes, checklist
│   │   │   │   ├── chat.py                  ← RAG query endpoint
│   │   │   │   └── auth.py                  ← Auth middleware (Supabase JWT)
│   │   │   └── deps.py                      ← Shared FastAPI dependencies
│   │   │
│   │   ├── models/
│   │   │   ├── document.py                  ← SQLAlchemy models
│   │   │   ├── organization.py
│   │   │   ├── clause.py
│   │   │   ├── playbook.py
│   │   │   ├── onboarding.py
│   │   │   └── user.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── document.py                  ← Pydantic request/response schemas
│   │   │   ├── playbook.py
│   │   │   ├── onboarding.py
│   │   │   └── chat.py
│   │   │
│   │   ├── services/
│   │   │   ├── ingestion/
│   │   │   │   ├── parser.py                ← Unstructured.io + PyMuPDF wrapper
│   │   │   │   ├── chunker.py               ← Semantic clause-boundary chunking
│   │   │   │   └── extractor.py             ← Raw text → section-labeled chunks
│   │   │   │
│   │   │   ├── nlp/
│   │   │   │   ├── ner.py                   ← LegalBERT NER: parties, dates, values
│   │   │   │   ├── classifier.py            ← CUAD clause type classification
│   │   │   │   ├── obligation.py            ← spaCy dependency parsing → obligations
│   │   │   │   └── pipeline.py              ← Orchestrates full NLP pass on a document
│   │   │   │
│   │   │   ├── distillation/
│   │   │   │   ├── synthesizer.py           ← Claude API: NLP output → structured JSON
│   │   │   │   ├── merger.py                ← Merge multi-doc output into org playbook
│   │   │   │   └── prompts.py               ← All distillation prompt templates
│   │   │   │
│   │   │   ├── generation/
│   │   │   │   ├── textbook.py              ← Claude API: playbook → 10-20 page textbook
│   │   │   │   ├── quiz.py                  ← Claude API: textbook → MCQ + scenario quizzes
│   │   │   │   ├── checklist.py             ← Claude API: playbook → contract review checklist
│   │   │   │   └── prompts.py               ← All generation prompt templates
│   │   │   │
│   │   │   ├── retrieval/
│   │   │   │   ├── embedder.py              ← Embed clauses → Qdrant
│   │   │   │   ├── retriever.py             ← RAG retrieval: query → top-k clauses
│   │   │   │   └── chat_service.py          ← Full RAG chat: query + history → response
│   │   │   │
│   │   │   └── export/
│   │   │       ├── word_exporter.py         ← python-docx: playbook → .docx
│   │   │       └── pdf_exporter.py          ← fpdf2: playbook → .pdf
│   │   │
│   │   └── tasks/
│   │       ├── process_document.py          ← Celery task: full pipeline for one doc
│   │       ├── regenerate_playbook.py       ← Celery task: re-merge + regenerate after new doc
│   │       └── generate_onboarding.py       ← Celery task: generate textbook + quizzes
│   │
│   ├── alembic/                             ← DB migrations
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── (auth)/                          ← Deferred — auth added in later phase
│   │   │   │   └── [placeholder]
│   │   │   ├── dashboard/
│   │   │   │   ├── page.tsx                 ← Org dashboard: doc list, pipeline status
│   │   │   │   ├── upload/page.tsx          ← Document upload flow
│   │   │   │   ├── playbook/page.tsx        ← Org playbook viewer + export
│   │   │   │   └── settings/page.tsx
│   │   │   ├── onboarding/
│   │   │   │   ├── page.tsx                 ← New hire landing: textbook + quizzes
│   │   │   │   ├── textbook/page.tsx        ← Interactive textbook reader
│   │   │   │   ├── quiz/[id]/page.tsx       ← Interactive quiz screen
│   │   │   │   ├── checklist/page.tsx       ← Contract review checklist tool
│   │   │   │   └── chat/page.tsx            ← RAG chat: "ask the playbook"
│   │   │   └── layout.tsx
│   │   │
│   │   ├── components/
│   │   │   ├── upload/
│   │   │   │   ├── DropZone.tsx             ← Drag-and-drop file upload
│   │   │   │   ├── UploadProgress.tsx       ← Pipeline stage progress bar
│   │   │   │   └── DocumentCard.tsx
│   │   │   ├── playbook/
│   │   │   │   ├── PlaybookViewer.tsx       ← Structured playbook with section nav
│   │   │   │   ├── ClauseCard.tsx           ← Individual clause with confidence badge
│   │   │   │   ├── ExportButton.tsx         ← Download Word / PDF
│   │   │   │   └── VersionHistory.tsx
│   │   │   ├── onboarding/
│   │   │   │   ├── TextbookReader.tsx       ← Paginated textbook with progress
│   │   │   │   ├── QuizCard.tsx             ← MCQ / scenario question UI
│   │   │   │   ├── QuizResults.tsx          ← Score + explanations
│   │   │   │   ├── ChecklistTool.tsx        ← Interactive contract checklist (like image)
│   │   │   │   └── ChatInterface.tsx        ← RAG chat with source citations
│   │   │   ├── pipeline/
│   │   │   │   ├── PipelineStatus.tsx       ← Live job status (polling)
│   │   │   │   └── StageIndicator.tsx       ← Visual step: Ingesting → NLP → Distilling → Done
│   │   │   └── ui/                          ← shadcn/ui primitives
│   │   │
│   │   ├── lib/
│   │   │   ├── api.ts                       ← Typed API client (fetch wrapper)
│   │   │   ├── supabase.ts                  ← Supabase client
│   │   │   └── utils.ts
│   │   │
│   │   └── types/
│   │       ├── document.ts
│   │       ├── playbook.ts
│   │       └── onboarding.ts
│   │
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml                       ← Local dev: FastAPI + Redis + Qdrant + Postgres
└── README.md
```

---

## 2. Data Flow

**Core principle**: Two separate pipelines — Pipeline A produces the org artifact (playbook); Pipeline B consumes it to produce training material. Both are async, tracked by job IDs.

### A. Document Upload Flow

1. User drags/drops PDF or DOCX files onto the upload zone
2. Frontend calls `POST /api/documents/upload` (multipart form)
3. Backend stores raw file to **Supabase Storage** (`org_id/documents/filename`)
4. Backend creates a `Document` record in PostgreSQL: `status = "pending"`
5. Backend enqueues a **Celery task**: `process_document.delay(document_id)`
6. Frontend receives `{ document_id, job_id }` and begins polling `GET /api/pipeline/status/{job_id}`
7. `PipelineStatus` component shows live stage progression

### B. NLP Processing Pipeline (Celery Worker)

For each document, the `process_document` Celery task runs:

1. **Ingestion** (`parser.py`)
   - Download raw file from Supabase Storage
   - Unstructured.io partitions the document → list of `Element` objects (Title, NarrativeText, Table, etc.)
   - Preserves heading hierarchy → maps to contract sections

2. **Semantic Chunking** (`chunker.py`)
   - Group elements by legal clause boundaries (not token count)
   - Each chunk = one logical clause with its heading context
   - Output: `List[RawClause]` — `{ text, section_path, page_number, char_offset }`

3. **NLP Pass** (`nlp/pipeline.py`)
   - **NER** (LegalBERT): tag parties, dates, monetary values, jurisdictions, defined terms
   - **Clause Classification** (CUAD-RoBERTa): label each clause type from 41 CUAD categories (indemnification, liability cap, governing law, IP ownership, termination for convenience, etc.)
   - **Obligation Extraction** (spaCy dep-parse): extract `(party, must/shall/may, action, condition)` tuples
   - Output: `List[ProcessedClause]` — enriched with NER tags, clause type label, obligations

4. **Embedding** (`embedder.py`)
   - Embed each `ProcessedClause` using `BAAI/bge-m3`
   - Upsert to **Qdrant** collection scoped to `org_id`
   - Store clause metadata in PostgreSQL `clauses` table

5. Update `Document.status = "nlp_complete"`

### C. Distillation Flow (Admin-Triggered)

After documents are processed, an admin manually triggers playbook regeneration via `POST /api/playbook/regenerate`. This is intentional — new documents don't automatically change the playbook without a human deciding it's time to rebuild.

1. Admin clicks "Regenerate Playbook" in the dashboard
2. Group by CUAD clause type across all documents
3. For each clause type group, call **Claude API** (`synthesizer.py`):
   - Prompt: "Given these N examples of [clause_type] clauses from this org's contracts, identify: (a) absolute non-negotiables, (b) standard positions, (c) acceptable variations, (d) red flags. Return structured JSON."
   - Claude returns structured `PlaybookSection` JSON
4. `merger.py` combines all `PlaybookSection` objects into a single `OrgPlaybook`
5. Persist updated `OrgPlaybook` to PostgreSQL (versioned — every update creates a new version)
6. Update `Document.status = "distilled"`

### D. Content Generation Flow (Celery Worker)

After distillation, `generate_onboarding` task runs (or triggered manually):

1. Pull current `OrgPlaybook` from PostgreSQL
2. **Textbook generation** (`textbook.py`):
   - Claude API: "Given this org playbook, generate a 10-20 page onboarding textbook structured as: Introduction → Key Parties & Definitions → [one chapter per major clause type] → Red Flags & Common Mistakes → Summary"
   - Returns `TextbookContent` with sections, explanatory prose, examples
3. **Quiz generation** (`quiz.py`):
   - Claude API generates 3 quiz types per textbook chapter:
     - MCQ (4 options, 1 correct, explanation included)
     - True/False with explanation
     - Scenario: "You're reviewing a contract and see [clause excerpt]. What should you flag?"
   - Returns `QuizSet` with questions, answers, explanations
4. **Checklist generation** (`checklist.py`):
   - Claude API generates a contract review checklist modeled on the image provided
   - Structured as: Category → Item/Clause → Check Point / Review Question
   - Categories pulled from CUAD taxonomy + org-specific non-negotiables
5. Persist all generated content to PostgreSQL
6. Update `OrgPlaybook.onboarding_ready = true`

### E. Interactive Query Flow (RAG Chat)

1. New hire types a question in `ChatInterface`
2. Frontend calls `POST /api/chat/query` with `{ question, conversation_history }`
3. `chat_service.py`:
   - Embed the question using `BAAI/bge-m3`
   - Retrieve top-5 most relevant `ProcessedClause` objects from Qdrant (scoped to org)
   - Build context: retrieved clauses + conversation history
   - Call Claude API: "Based on this org's actual contract clauses [retrieved context], answer: [question]. Cite the source clause and section."
   - Claude returns answer with inline citations
4. Frontend renders response with source clause cards that can be expanded

### F. Export Flow

1. User clicks "Export Playbook" on dashboard
2. `POST /api/playbook/export` with `{ format: "docx" | "pdf" }`
3. Backend pulls current `OrgPlaybook` JSON
4. `word_exporter.py` or `pdf_exporter.py` generates the file
5. Returns a signed Supabase Storage URL with 15-minute expiry
6. Frontend triggers download

---

## 3. Data Structures

```
Organization
├── id: UUID
├── name: str
├── industry: str  ← "engineering" | "legal" | "real_estate" | "tech" | "other"
├── size: str      ← "small" | "medium"
├── created_at: datetime
└── playbook_id: UUID (FK → OrgPlaybook, nullable)

User
├── id: UUID (mirrors Supabase Auth user)
├── org_id: UUID (FK → Organization)
├── email: str
├── role: "admin" | "lawyer" | "new_hire" | "reviewer"
├── created_at: datetime
└── onboarding_progress: OnboardingProgress (JSON)

Document
├── id: UUID
├── org_id: UUID
├── filename: str
├── doc_type: "master_agreement" | "compliance" | "nda" | "sow" | "other"
├── storage_path: str  ← Supabase Storage key
├── upload_date: datetime
├── status: "pending" | "ingesting" | "nlp_processing" | "distilling" | "complete" | "error"
├── job_id: str  ← Celery task ID for polling
├── page_count: int
├── error_message: str | None
└── metadata: dict  ← extracted title, parties, date from NER

RawClause
├── id: UUID
├── document_id: UUID
├── org_id: UUID
├── text: str
├── section_path: list[str]  ← ["Article III", "Section 3.2", "Subsection (b)"]
├── page_number: int
└── char_offset: int

ProcessedClause
├── id: UUID
├── raw_clause_id: UUID
├── org_id: UUID
├── clause_type: str  ← CUAD label: "Indemnification" | "Liability Cap" | "IP Ownership" | ...
├── clause_type_confidence: float
├── entities: dict  ← {parties: [], dates: [], amounts: [], jurisdictions: []}
├── obligations: list[Obligation]
│   └── Obligation: {party, modal_verb, action, condition, is_mandatory: bool}
├── embedding_id: str  ← Qdrant point ID
└── raw_text: str

OrgPlaybook
├── id: UUID
├── org_id: UUID
├── version: int  ← increments on every regeneration
├── generated_at: datetime
├── is_current: bool
├── sections: list[PlaybookSection]
├── onboarding_ready: bool
└── doc_count: int  ← number of documents that contributed

PlaybookSection
├── clause_type: str  ← CUAD category
├── title: str  ← human-readable e.g. "Indemnification & Liability"
├── non_negotiables: list[str]  ← absolute requirements from this org's history
├── standard_positions: list[StandardPosition]
│   └── StandardPosition: {description, acceptable_range, rationale}
├── red_flags: list[str]  ← patterns to flag during review
├── industry_baseline: str  ← what's typical for this sector
├── example_clauses: list[str]  ← sanitized excerpts from actual docs
└── source_doc_ids: list[UUID]

TextbookContent
├── id: UUID
├── org_id: UUID
├── playbook_id: UUID  ← which playbook version this was generated from
├── generated_at: datetime
├── page_estimate: int  ← 10-20
├── chapters: list[TextbookChapter]
│   └── TextbookChapter:
│       ├── title: str
│       ├── chapter_number: int
│       ├── content: str  ← markdown prose
│       ├── key_takeaways: list[str]
│       ├── clause_type: str | None  ← links back to PlaybookSection
│       └── quiz_id: UUID | None

QuizSet
├── id: UUID
├── org_id: UUID
├── chapter_id: UUID | None
├── quiz_type: "chapter_review" | "scenario" | "final_assessment"
├── questions: list[Question]
└── generated_at: datetime

Question
├── id: UUID
├── quiz_id: UUID
├── question_type: "mcq" | "true_false" | "scenario"
├── text: str
├── context: str | None  ← for scenario questions: the contract excerpt
├── options: list[str] | None  ← for MCQ
├── correct_answer: str
├── explanation: str  ← why this answer is correct — this is the learning moment
└── clause_type: str  ← which PlaybookSection this tests

ContractChecklist
├── id: UUID
├── org_id: UUID
├── playbook_id: UUID
├── generated_at: datetime
├── categories: list[ChecklistCategory]
│   └── ChecklistCategory:
│       ├── name: str  ← "I. Tender Submission & Execution Preliminaries"
│       ├── subcategories: list[ChecklistSubcategory]
│       │   └── ChecklistSubcategory:
│       │       ├── name: str  ← "A. Documents & Dates"
│       │       └── items: list[ChecklistItem]
│       │           └── ChecklistItem:
│       │               ├── item_clause: str  ← "Tender/Contract Name"
│       │               ├── review_question: str  ← "Is the official name or title noted and correct?"
│       │               ├── is_non_negotiable: bool  ← red if org's non-negotiable
│       │               └── clause_type: str  ← links to PlaybookSection

OnboardingProgress
├── user_id: UUID
├── textbook_chapters_read: list[int]
├── quizzes_completed: list[UUID]
├── quiz_scores: dict[UUID, float]
├── checklist_uses: int
├── chat_queries: int
└── completion_percentage: float

ChatMessage
├── id: UUID
├── session_id: UUID
├── user_id: UUID
├── role: "user" | "assistant"
├── content: str
├── source_clauses: list[UUID]  ← which ProcessedClauses were retrieved
└── created_at: datetime

PipelineJob
├── job_id: str  ← Celery task ID
├── document_id: UUID
├── org_id: UUID
├── stage: "queued" | "ingesting" | "nlp" | "distilling" | "generating" | "complete" | "error"
├── progress_pct: int
├── started_at: datetime
├── completed_at: datetime | None
└── error: str | None
```

---

## 4. Deliverables & Implementation Steps

### Phase 1 — Core Pipelines (MVP)

**Goal**: End-to-end pipeline from document upload through distillation, with both outputs (org playbook + basic onboarding content) generated and viewable. No quiz interactivity yet.

#### 1.1 Project Setup

- **1.1.1** Initialize monorepo: `backend/` (FastAPI) + `frontend/` (Next.js)
- **1.1.2** `docker-compose.yml` with services: `api`, `worker` (Celery), `redis`, `qdrant`, `postgres`
- **1.1.3** Supabase project: create tables, storage bucket `documents`, enable RLS
- **1.1.4** FastAPI skeleton: `main.py`, CORS, health check endpoint, router registration
- **1.1.5** Next.js skeleton: `layout.tsx`, Supabase client, API client (`lib/api.ts`)
- **1.1.6** Alembic setup: initial migration with all tables
- **1.1.7** Environment config: `.env.example` documenting all required vars

#### 1.2 Authentication

- **1.2.1** Supabase Auth: email/password + magic link flows
- **1.2.2** Next.js: login page, signup page with org creation, auth middleware for protected routes
- **1.2.3** FastAPI: JWT validation middleware (`deps.py` `get_current_user`)
- **1.2.4** Org isolation: all DB queries scoped to `org_id` extracted from JWT
- **1.2.5** Role-based access: `admin`/`lawyer` can upload + see playbook; `new_hire` sees onboarding only

#### 1.3 Document Upload

- **1.3.1** `DropZone.tsx`: drag-and-drop + file browser, accepts PDF/DOCX, shows file size + type
- **1.3.2** `DocumentCard.tsx`: filename, doc type selector, upload date, status badge
- **1.3.3** `POST /api/documents/upload`: multipart upload → Supabase Storage → DB record → enqueue task
- **1.3.4** `GET /api/documents/`: list org's documents with status
- **1.3.5** `DELETE /api/documents/{id}`: soft delete, trigger playbook regeneration
- **1.3.6** File validation: max 50MB, PDF/DOCX only, virus-scan stub (log warning, skip for MVP)

#### 1.4 Pipeline Status Tracking

- **1.4.1** `PipelineJob` table + Celery task hooks that update stage on each transition
- **1.4.2** `GET /api/pipeline/status/{job_id}`: returns `{ stage, progress_pct, error }`
- **1.4.3** `StageIndicator.tsx`: horizontal stepper — Uploading → Parsing → NLP → Distilling → Ready
- **1.4.4** `PipelineStatus.tsx`: polling every 3 seconds via `setInterval`, updates StageIndicator
- **1.4.5** Error state: show error message + "Retry" button

#### 1.5 Ingestion Service

- **1.5.1** Install `unstructured[pdf,docx]` — handles both formats natively
- **1.5.2** `parser.py`:
  - `parse_document(file_path: str) -> list[Element]`
  - Categorize by element type: Title, NarrativeText, Table, ListItem
  - Preserve section hierarchy using heading levels
- **1.5.3** `chunker.py`:
  - `chunk_by_clause(elements: list[Element]) -> list[RawClause]`
  - Split at clause-boundary headings (numbered articles, section headers)
  - Minimum chunk size: 100 tokens; maximum: 1500 tokens (to stay within Claude context budget per clause)
  - Preserve section_path: `["Article III - Representations", "Section 3.2"]`
- **1.5.4** `extractor.py`:
  - Run Unstructured OCR fallback for scanned PDFs
  - Clean common OCR artifacts (ligatures, hyphenation, unicode noise)
- **1.5.5** Persist `RawClause` records to PostgreSQL

#### 1.6 NLP Service

- **1.6.1** Load models at worker startup (not per-request):
  - `spaCy`: `en_core_web_trf`
  - `LegalBERT`: `nlpaueb/legal-bert-base-uncased` via HuggingFace
  - CUAD classifier: fine-tuned `roberta-base` checkpoint on CUAD dataset (download from HuggingFace Hub: `theatticusproject/cuad-roberta`)
- **1.6.2** `ner.py`:
  - `extract_entities(text: str) -> dict` → `{parties, dates, amounts, jurisdictions, defined_terms}`
  - Use LegalBERT NER pipeline via `transformers.pipeline("ner", model=..., aggregation_strategy="simple")`
- **1.6.3** `classifier.py`:
  - `classify_clause(text: str) -> tuple[str, float]` → `(clause_type, confidence)`
  - Run CUAD model: returns one of 41 clause type labels
  - Confidence threshold: if < 0.5, label as `"unclassified"`
- **1.6.4** `obligation.py`:
  - `extract_obligations(text: str) -> list[Obligation]`
  - spaCy dep parse: find modal verbs (shall, must, may, will, agrees to)
  - Build `(subject, modal, action, condition)` from dependency tree
- **1.6.5** `nlp/pipeline.py`:
  - `process_clause(raw: RawClause) -> ProcessedClause`
  - Orchestrates NER + classification + obligation extraction
  - Handles exceptions per-clause (log + skip, don't fail entire document)
- **1.6.6** Embed `ProcessedClause.raw_text` → upsert to Qdrant with payload: `{org_id, clause_type, doc_id}`

#### 1.7 Distillation Service

- **1.7.1** `synthesizer.py` — per clause type:
  ```
  System: "You are a legal knowledge engineer. You will receive multiple examples of the same 
  clause type from a company's actual contracts. Extract: (1) non-negotiables — terms they 
  always insist on, (2) standard positions — their typical language, (3) acceptable variations, 
  (4) red flags — patterns that appear in bad outcomes. Return ONLY valid JSON."
  ```
  - Batch clauses by type (max 20 per Claude call to stay within budget)
  - Parse JSON response → `PlaybookSection`
  - Retry on JSON parse failure (up to 3x with temperature lowered)
- **1.7.2** `merger.py`:
  - Collect all `PlaybookSection` objects across all clause types
  - Deduplicate non-negotiables (exact match + semantic similarity)
  - Produce final `OrgPlaybook` JSON
- **1.7.3** Version the playbook: every regeneration creates a new version record; only latest has `is_current = True`
- **1.7.4** `GET /api/playbook/current`: return latest `OrgPlaybook` for org

#### 1.8 Content Generation

- **1.8.1** `textbook.py`:
  - System prompt establishes persona: "legal training writer for non-specialist professionals"
  - Chapter structure: Introduction → Definitions → [one chapter per major clause type in playbook] → Red Flags → Summary
  - Per-chapter call to Claude API (not one giant call) — avoids context limits, allows retry
  - Output: markdown with clear headings, bullet takeaways, inline examples
  - Target: 10-20 pages (approx 4,000–8,000 words)
- **1.8.2** `quiz.py`:
  - One `QuizSet` per chapter (3-5 questions each)
  - MCQ: 4 options, 1 correct, full explanation for every option
  - Scenario: provide real clause excerpt from org's docs; ask what to flag
  - Final assessment: 10-question cumulative quiz mixing all types
- **1.8.3** `checklist.py`:
  - Generate structured checklist matching the format in the uploaded image
  - Categories from CUAD taxonomy + org non-negotiables
  - Mark items that are org-specific non-negotiables with a flag
- **1.8.4** Persist all generated content; link to `playbook_id` so content versioning is tracked

#### 1.9 Playbook Viewer (Frontend)

- **1.9.1** `PlaybookViewer.tsx`:
  - Left sidebar: section navigation by clause type
  - Main panel: `PlaybookSection` rendered with non-negotiables, standard positions, red flags
  - Non-negotiables highlighted in red; acceptable variations in green
  - "Last updated" badge showing version + date
- **1.9.2** `ClauseCard.tsx`:
  - Shows clause type label, confidence badge, source document reference
  - Expandable to show full extracted text
- **1.9.3** `ExportButton.tsx`:
  - "Export as Word" + "Export as PDF" buttons
  - Calls export endpoint → polls for signed URL → triggers download
- **1.9.4** `VersionHistory.tsx`:
  - Dropdown showing all playbook versions with timestamps and doc counts
  - Can view (read-only) any historical version

#### 1.10 Onboarding Layer (Frontend)

- **1.10.1** `TextbookReader.tsx`:
  - Paginated view (chapter = page) with prev/next navigation
  - Progress bar: "Chapter 3 of 8 — 37% complete"
  - Mark chapter as read → updates `OnboardingProgress`
  - Key takeaways rendered as a highlighted box at chapter end
- **1.10.2** `ChecklistTool.tsx`:
  - Renders `ContractChecklist` as an interactive table matching the image format
  - Each row: checkbox + Category + Item/Clause + Review Question
  - Checkboxes are session-local (not persisted — tool is reusable per contract)
  - Non-negotiable items highlighted with a subtle red left border
  - Export completed checklist as PDF
- **1.10.3** Basic `QuizCard.tsx` (static for Phase 1 — interactivity in Phase 2)

---

### Phase 2 — Interactive Layer

**Goal**: Quiz interactivity, RAG chat interface, onboarding progress tracking, and admin controls.

#### 2.1 Interactive Quizzes

- **2.1.1** `QuizCard.tsx` — full interactivity:
  - MCQ: click to select, submit → reveal correct/wrong with color
  - Explanation always shown after submission
  - True/False: two-button UI
  - Scenario: text + clause excerpt, free-select or MCQ
- **2.1.2** `QuizResults.tsx`:
  - Score: X/N correct
  - Per-question breakdown: what you answered vs. correct + explanation
  - "Retry" button resets question order (questions randomized each attempt)
- **2.1.3** Score persistence: `PATCH /api/onboarding/progress` after each quiz
- **2.1.4** Admin view: see all new hire progress scores in a table

#### 2.2 RAG Chat Interface

- **2.2.1** `ChatInterface.tsx`:
  - Input field + send button
  - Message bubbles: user (right) + assistant (left)
  - Source clause cards shown beneath each assistant message — expandable
  - Suggested questions shown on first load: "What are our non-negotiables on indemnification?" / "What's our standard position on governing law?"
- **2.2.2** `chat_service.py`:
  - Embed query → retrieve top-5 Qdrant clauses (filtered by `org_id`)
  - Build prompt: system (org legal assistant persona) + retrieved context + conversation history (last 5 turns) + question
  - Claude API call with streaming (SSE)
  - Frontend: SSE-based streaming render
- **2.2.3** Conversation history: persist `ChatMessage` records per session

#### 2.3 Onboarding Progress Dashboard

- **2.3.1** New hire home page: progress rings for Textbook / Quizzes / Checklist
- **2.3.2** Admin dashboard: table of all new hires with completion %
- **2.3.3** Completion badge: "Onboarding Complete" when textbook 100% + all quizzes passed

---

### Phase 3 — Polish, Scale, & Reliability

**Goal**: Production-readiness, multi-org robustness, and advanced features.

#### 3.1 Production Hardening

- Rate limiting on API (especially Claude API calls — expensive)
- Token budget tracking per org (warn when approaching limits)
- Retry/dead-letter queue for failed Celery tasks
- Comprehensive error messages in pipeline status

#### 3.2 Human-in-the-Loop Review

- `ReviewWorkflow`: admin lawyer can review + edit any `PlaybookSection` before it goes live
- Edits saved as `manual_overrides` — preserved across playbook regenerations
- "Approved by [name] on [date]" badge on approved sections
- New hires see only approved playbooks

#### 3.3 Advanced Checklist

- Checklist templates: org can create custom checklist templates for different contract types
- Pre-fill from uploaded contract: paste a contract, AI fills in the checklist answers
- Export options: Excel, PDF, shareable link

---

## 5. Technical Implementation Details

### Token Budget Strategy

The core insight is: **distill once, query against the distillation**. Never send raw contracts to Claude.

| Operation | Input | Approx Tokens | Cost Mitigation |
|-----------|-------|---------------|----------------|
| Clause synthesis (per clause type) | 20 × ~300 token clauses | ~7,000 | Batch by type; cache result |
| Textbook chapter generation | `PlaybookSection` JSON (~1,500 tokens) | ~3,000/chapter | Per-chapter calls, not one monolith |
| Quiz generation | Chapter text (~2,000 tokens) | ~4,000/quiz set | Generate on demand, cache |
| RAG chat | Top-5 clauses (~1,500) + history (~1,000) | ~4,000/query | Context window is manageable |

### NLP Model Loading Strategy

Models are large — load once at Celery worker startup, not per-task:

```python
# celery_app.py — runs once per worker process
@worker_ready.connect
def load_models(**kwargs):
    from services.nlp.ner import NERService
    from services.nlp.classifier import ClauseClassifier
    NERService.initialize()      # LegalBERT: ~400MB
    ClauseClassifier.initialize()  # CUAD-RoBERTa: ~500MB
```

### Multi-Tenancy & Data Isolation

- All PostgreSQL tables have `org_id UUID NOT NULL` with index
- Supabase RLS policies: every table enforces `org_id = auth.jwt() ->> 'org_id'`
- Qdrant: all vectors tagged with `org_id` payload; all queries filter by `org_id`
- Supabase Storage: bucket paths are `{org_id}/documents/{doc_id}/{filename}`

### Key API Endpoints

```
POST   /api/auth/signup                 ← Create org + admin user
POST   /api/auth/login                  ← Supabase auth

POST   /api/documents/upload            ← Upload file, enqueue pipeline
GET    /api/documents/                  ← List org documents
DELETE /api/documents/{id}              ← Soft delete

GET    /api/pipeline/status/{job_id}    ← Poll pipeline progress

GET    /api/playbook/current            ← Current org playbook
GET    /api/playbook/versions           ← All playbook versions
POST   /api/playbook/export             ← Generate + return Word/PDF download URL
PATCH  /api/playbook/sections/{clause_type}  ← Human override of a section

GET    /api/onboarding/textbook         ← Full textbook content
GET    /api/onboarding/quizzes          ← All quiz sets
GET    /api/onboarding/checklist        ← Generated contract checklist
PATCH  /api/onboarding/progress         ← Update new hire progress

POST   /api/chat/query                  ← RAG chat query (streaming SSE)
GET    /api/chat/history                ← Conversation history
```

### CUAD Clause Type Mapping

The 41 CUAD clause types are grouped for the playbook UI:

| Display Category | CUAD Labels |
|-----------------|-------------|
| Parties & Authorization | Parties, Signatories |
| Scope & Deliverables | Scope of Work, Deliverables, Specifications |
| Time & Milestones | Term, Renewal, Milestones |
| Payment | Contract Amount, Payment Terms, Price Adjustment |
| Liability | Indemnification, Liability Cap, Warranty |
| IP & Confidentiality | IP Ownership, License Grant, NDA/Confidentiality |
| Termination | Termination for Convenience, Termination for Cause |
| Governing Law | Jurisdiction, Dispute Resolution, Arbitration |
| Change Management | Change Order, Amendments |

---

## 6. Demo Flow (5 Minutes)

**Pre-setup**: Two documents pre-uploaded and processed. Demo org: "Ironbridge Engineering Ltd." New hire persona: first-week paralegal.

| Time | What to Show | Script |
|------|-------------|--------|
| **0:00 – 0:30** | Upload screen — drag 2 docs | "Ironbridge Engineering has 5 years of master service agreements and compliance docs. Drag them in." |
| **0:30 – 1:00** | Pipeline status — live stages | "Watch the pipeline: Parsing... NLP classifying 47 clauses... Distilling into your org's DNA. Takes about 90 seconds. You'd do this once when onboarding a new legal hire." |
| **1:00 – 1:45** | **Org Playbook** — non-negotiables | "This is what the AI found in your contracts. Indemnification — your non-negotiable: liability always capped at contract value. Governing law — always Ontario. Red flag: 'mutual indemnification' with no cap — you've rejected it twice." |
| **1:45 – 2:15** | Export playbook as Word | "One click. Word document. 18 pages. Senior lawyer reviews, approves, it's locked." |
| **2:15 – 3:00** | **Textbook** — new hire view | "Switch to Sarah's view — first week as a junior in-house paralegal. Chapter 3: Indemnification. Plain language. Real examples from your actual contracts. Not a law school textbook — your organization's way of doing things." |
| **3:00 – 3:30** | **Quiz** — scenario question | "End of chapter quiz. 'You're reviewing a contract. The indemnification clause has no liability cap. What do you do?' Sarah selects Flag for Review. Correct — here's why, with the citation from your playbook." |
| **3:30 – 4:15** | **Contract Checklist** | "Sarah gets a new contract to review. She opens the checklist — auto-generated from your org's standards. Categories, clauses, review questions. Your non-negotiables are highlighted. She works through it methodically. No senior lawyer needed." |
| **4:15 – 4:45** | **RAG Chat** | "'What's our standard position on termination for convenience?' Instant answer, sourced from your actual clauses. Not generic legal AI — your org's institutional knowledge." |
| **4:45 – 5:00** | Admin progress view | "Admin sees Sarah's progress: Chapter 5 of 8, quiz scores, 12 chat queries. You know she's ready before she's ever near a real contract." |

**Hero moments:**
1. The org playbook self-generating from raw documents (1:00–1:45) — "this would take a senior partner a week"
2. Scenario quiz with real org clause excerpts (3:00–3:30) — "training material that actually reflects how you operate"
3. RAG chat citing specific clauses (4:15–4:45) — "institutional knowledge that doesn't leave when someone does"

---

## 7. Success Criteria

### Primary Metric
A new hire can complete onboarding, pass all quizzes, and use the checklist to review a real contract — without a single hour of senior lawyer time.

### Phase 1 (MVP) Criteria

**Ingestion Pipeline**:
- [ ] PDF and DOCX uploads work for files up to 50MB
- [ ] Parser preserves section hierarchy (Article → Section → Subsection)
- [ ] Clauses are chunked at logical boundaries, not arbitrary token counts
- [ ] Pipeline status updates in real-time (polling works)

**NLP**:
- [ ] LegalBERT extracts parties, dates, and monetary amounts with >80% accuracy on test docs
- [ ] CUAD classifier assigns a clause type with confidence score for >75% of clauses
- [ ] Obligations extracted as subject-verb-action tuples for clauses containing "shall"/"must"

**Distillation**:
- [ ] Org playbook generates within 3 minutes for a 50-page document set
- [ ] Non-negotiables section is non-empty and coherent for at least 5 clause types
- [ ] New playbook version generated on every document addition/deletion

**Generation**:
- [ ] Textbook is 10-20 pages (4,000-8,000 words), chaptered, readable by a non-lawyer
- [ ] Each chapter has at least 3 key takeaways
- [ ] Quiz has at least 3 questions per chapter with explanations
- [ ] Contract checklist matches the category/item/review-question format

**Frontend**:
- [ ] Playbook viewer renders all sections with non-negotiables highlighted
- [ ] Export to Word produces a well-formatted, downloadable document
- [ ] Textbook reader shows chapter progress
- [ ] Checklist is interactive (checkboxes) and exportable

**Overall**:
- [ ] Full pipeline (upload → playbook ready) completes in under 5 minutes for a 2-doc test set
- [ ] Multi-tenancy: org A cannot see org B's data (verified with two test orgs)
- [ ] Human-in-the-loop: playbook marked as "pending review" until admin approves

---

## 8. Future Enhancements (AI-Powered)

### Continuous Learning
- Playbook auto-updates when new contracts are uploaded (background job)
- Drift detection: alert admins when new contracts contradict established non-negotiables
- Version diff view: "What changed in v4 vs v3 of your playbook?"

### Contract Pre-Fill & Review
- Upload a new contract being reviewed → checklist auto-filled based on what the AI reads
- Red flag highlighting directly on the contract PDF
- Gap analysis: "This contract is missing your standard IP clause"

### Industry Benchmarking
- Anonymized aggregate: "Your liability cap is 20% lower than sector average"
- Template library: generate a first-draft clause matching your org's standard position

### Multi-Format Support
- Email thread ingestion: extract negotiation history from email chains
- Slack/Teams integration: query the playbook from within messaging apps
- Notion/Confluence export: push playbook into existing knowledge bases

### Advanced Onboarding
- Role-specific training tracks: PM, paralegal, board treasurer each get tailored content
- Competency certification: pass all quizzes → downloadable certificate
- Adaptive quizzes: harder questions for experienced hires, simpler for non-legal staff
