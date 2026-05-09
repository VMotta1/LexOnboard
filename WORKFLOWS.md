# LexOnboard — Solo Developer Workflows for Claude Code

> **Single-engineer build guide.** Each workflow is a self-contained Claude Code prompt. Run them in order. Each workflow owns specific files and assumes the previous one is committed and pushed. Paste the prompt block directly into Claude Code.

---

## Developer Setup

| Item | Detail |
|------|--------|
| **Stack** | FastAPI (Python 3.11) + Next.js 14 (TypeScript) |
| **Local dev** | Docker Compose (Postgres, Redis, Qdrant, API, Worker, Frontend) |
| **Branch strategy** | `main` = always deployable. Feature branches per workflow: `workflow-N/description` |
| **Commit cadence** | Commit at the end of each sub-task (not each workflow) |
| **Environment** | `.env.local` (frontend) + `.env` (backend) — never committed |

---

## Pre-Workflow: Project Initialization

> **Run this once before any workflow. Do it yourself, not via Claude Code.**

```bash
# Create monorepo
mkdir lexonboard && cd lexonboard
git init

# Backend
mkdir backend && cd backend
python3.11 -m venv venv && source venv/bin/activate
pip install fastapi uvicorn[standard] sqlalchemy alembic psycopg2-binary \
  python-dotenv pydantic-settings celery[redis] redis \
  anthropic langchain langchain-community \
  "unstructured[pdf,docx,local-inference]" spacy transformers torch \
  pytesseract pillow pdf2image \
  python-docx fpdf2 qdrant-client httpx python-multipart sentence-transformers
# OCR system dependency (run separately):
# brew install tesseract poppler   ← macOS
# apt-get install tesseract-ocr poppler-utils   ← Linux/Docker
python -m spacy download en_core_web_sm
cd ..

# Frontend
npx create-next-app@14 frontend --typescript --tailwind --app --src-dir --import-alias "@/*"
cd frontend && npm install \
  lucide-react @radix-ui/react-dialog @radix-ui/react-tabs \
  framer-motion react-dropzone sonner uuid
cd ..

# Docker Compose
touch docker-compose.yml .env .env.example README.md
```

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: lexonboard
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
  api:
    build: ./backend
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    env_file: .env
    depends_on: [postgres, redis, qdrant]
  worker:
    build: ./backend
    command: celery -A app.celery_app worker --loglevel=info
    volumes:
      - ./backend:/app
    env_file: .env
    depends_on: [postgres, redis, qdrant]
volumes:
  qdrant_data:
```

---

## Workflow 1 — Backend Foundation

**Branch**: `workflow-1/backend-foundation`
**Owns**: `backend/app/main.py`, `backend/app/config.py`, `backend/app/database.py`, `backend/app/celery_app.py`, `backend/alembic/`, `backend/app/models/`, `backend/app/schemas/`, `backend/app/api/deps.py`

---

**Claude Code Prompt:**

```
You are building the backend foundation for LexOnboard, an AI-powered legal contract onboarding platform. The stack is FastAPI (Python 3.11), PostgreSQL via SQLAlchemy, Supabase for auth, Celery + Redis for async tasks, and Qdrant for vector storage.

Build the following in order. Commit after each section.

PROJECT STRUCTURE to create under backend/app/:
  main.py, config.py, database.py, celery_app.py
  models/ (document.py, organization.py, clause.py, playbook.py, onboarding.py, user.py)
  schemas/ (document.py, playbook.py, onboarding.py, chat.py)
  api/deps.py

--- SECTION 1: Config and App Entry ---

config.py — Pydantic BaseSettings pulling from .env:
  DATABASE_URL, REDIS_URL, QDRANT_URL, QDRANT_API_KEY (optional)
  ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY
  SUPABASE_STORAGE_BUCKET = "documents"
  ENVIRONMENT = "development" | "production"

main.py — FastAPI app:
  CORS middleware allowing localhost:3000 and production frontend domain
  Health check endpoint GET /health → {"status": "ok", "environment": ...}
  Include routers from api/routes/ (stub files for now)
  Lifespan handler: create DB tables on startup, log startup message

celery_app.py — Celery setup:
  Broker and backend both use REDIS_URL
  Auto-discover tasks from app.tasks
  Worker signals: on worker_ready, log that NLP models will be loaded here (stub)

--- SECTION 2: Database Models ---

All SQLAlchemy models use UUID primary keys (server_default=text("gen_random_uuid()")).
All tables include org_id UUID NOT NULL with index for multi-tenancy.
Use timezone-aware datetimes (DateTime(timezone=True)).

models/organization.py — Organization:
  id, name, industry (str), size ("small"|"medium"), created_at, plan ("trial"|"pro")

models/user.py — User:
  id (matches Supabase Auth UUID), org_id (FK Organization), email, role 
  role: "admin" | "lawyer" | "new_hire" | "reviewer"
  created_at, last_active

models/document.py — Document:
  id, org_id, filename, doc_type ("master_agreement"|"compliance"|"nda"|"sow"|"other")
  storage_path, upload_date, status, job_id (Celery task ID)
  page_count (nullable int), error_message (nullable text)
  metadata_ (JSON) — extracted parties, title, date from NER
  is_deleted (bool, default False) — soft delete

models/clause.py — Two models:
  RawClause: id, document_id (FK), org_id, text (Text), section_path (JSON array of strings),
    page_number, char_offset
  ProcessedClause: id, raw_clause_id (FK), org_id, clause_type (str), clause_type_confidence (float),
    entities (JSON), obligations (JSON array), embedding_id (str, nullable), raw_text (Text)

models/playbook.py — Two models:
  OrgPlaybook: id, org_id, version (int), generated_at, is_current (bool),
    sections (JSON — list of PlaybookSection dicts), onboarding_ready (bool, default False),
    doc_count (int)
  PlaybookEdit: id, playbook_id (FK OrgPlaybook), clause_type (str), 
    edited_by (FK User), edit_data (JSON), created_at, approved (bool)

models/onboarding.py — Four models:
  TextbookContent: id, org_id, playbook_id (FK), generated_at, page_estimate (int),
    chapters (JSON — list of chapter dicts)
  QuizSet: id, org_id, chapter_index (nullable int), quiz_type (str), 
    questions (JSON — list of question dicts), generated_at, playbook_id (FK)
  ContractChecklist: id, org_id, playbook_id (FK), generated_at,
    categories (JSON — list of category dicts)
  OnboardingProgress: id, user_id (FK, unique), org_id,
    chapters_read (JSON array of int), quizzes_completed (JSON array of UUID strings),
    quiz_scores (JSON dict), checklist_uses (int, default 0), chat_queries (int, default 0)
  ChatMessage: id, session_id (UUID), user_id (FK), org_id, role ("user"|"assistant"),
    content (Text), source_clause_ids (JSON array), created_at

--- SECTION 3: Alembic Setup ---

Initialize alembic in backend/ with env.py pointing to DATABASE_URL from config.
Create initial migration that generates all tables.
Add helper script backend/scripts/init_db.py that runs alembic upgrade head.

--- SECTION 4: Schemas ---

Pydantic v2 schemas (use model_config = ConfigDict(from_attributes=True)).

schemas/document.py:
  DocumentUploadResponse: id, filename, doc_type, status, job_id
  DocumentListItem: id, filename, doc_type, status, upload_date, page_count
  PipelineStatusResponse: job_id, stage, progress_pct, error (nullable), document_id

schemas/playbook.py:
  StandardPosition: description, acceptable_range, rationale
  PlaybookSectionSchema: clause_type, title, non_negotiables (list[str]), 
    standard_positions (list[StandardPosition]), red_flags (list[str]),
    industry_baseline (str), example_clauses (list[str]), source_doc_ids (list[str])
  OrgPlaybookResponse: id, version, generated_at, is_current, sections (list[PlaybookSectionSchema]),
    onboarding_ready, doc_count
  ExportRequest: format ("docx" | "pdf")
  ExportResponse: download_url, expires_at

schemas/onboarding.py:
  TextbookChapterSchema: title, chapter_number, content (markdown str), key_takeaways (list[str])
  TextbookResponse: id, chapters (list[TextbookChapterSchema]), page_estimate, generated_at
  QuestionSchema: id, question_type, text, context (nullable), options (nullable list[str]),
    correct_answer, explanation, clause_type
  QuizSetResponse: id, quiz_type, questions (list[QuestionSchema])
  ChecklistItemSchema: item_clause, review_question, is_non_negotiable, clause_type
  ChecklistSubcategorySchema: name, items (list[ChecklistItemSchema])
  ChecklistCategorySchema: name, subcategories (list[ChecklistSubcategorySchema])
  ContractChecklistResponse: id, categories (list[ChecklistCategorySchema])
  OnboardingProgressUpdate: chapters_read (list[int]), quiz_score (nullable — {quiz_id, score})
  OnboardingProgressResponse: chapters_read, quizzes_completed, quiz_scores, 
    checklist_uses, chat_queries, completion_percentage

schemas/chat.py:
  ChatQueryRequest: question (str), session_id (UUID), conversation_history (list[dict])
  SourceClause: id, clause_type, section_path (list[str]), excerpt (str)
  ChatResponse: answer (str), sources (list[SourceClause]), session_id

--- SECTION 5: Identity (No Auth — Dev Mode) ---

NOTE: Auth is deferred. For now, all endpoints accept org_id as a request header or query param.
This lets us build and test the full pipeline without auth friction. Auth will be added in a later phase.

api/deps.py:
  get_org_id(request: Request) -> str:
    Check header "X-Org-ID" first, then query param ?org_id=
    If missing: raise HTTPException 400 with message "X-Org-ID header is required"
    Return org_id string
  
  get_user_context(request: Request) -> dict:
    Returns a stub user context for now:
    org_id = get_org_id(request)
    user_id = request.headers.get("X-User-ID", "dev-user-001")
    role = request.headers.get("X-User-Role", "admin")
    Return {"user_id": user_id, "org_id": org_id, "role": role}
  
  NOTE: In every route that uses this, the docstring must say "# TODO: replace with real auth"

Create stub route files (return {"message": "not implemented"}) for:
  api/routes/documents.py, pipeline.py, playbook.py, onboarding.py, chat.py

Register all routers in main.py with prefix /api.

--- SECTION 6: Commit ---

git add -A && git commit -m "feat: backend foundation — models, schemas, celery, no-auth dev deps"
```

---

## Workflow 2 — Ingestion + NLP Pipeline

**Branch**: `workflow-2/ingestion-nlp`
**Owns**: `backend/app/services/ingestion/`, `backend/app/services/nlp/`, `backend/app/tasks/process_document.py`, `backend/app/api/routes/documents.py`, `backend/app/api/routes/pipeline.py`

---

**Claude Code Prompt:**

```
Continue building LexOnboard. Workflow 1 is complete — all models, schemas, Celery setup, and no-auth dev deps exist. Now build the document ingestion and NLP pipeline.

IMPORTANT: Auth is deferred. All routes use X-Org-ID header for org scoping. No JWT validation.

--- SECTION 1: Ingestion Services ---

services/ingestion/parser.py:
  parse_document(file_path: str, doc_type: str) -> list[dict]:
    Detect if PDF is text-based or image-based:
      Use PyMuPDF (fitz): open doc, check page.get_text() — if total extracted text < 100 chars 
      across first 3 pages, treat as image-based (scanned PDF).
    
    For text-based PDF:
      Use unstructured: partition_pdf(file_path, strategy="fast")
    
    For image-based / scanned PDF (OCR path):
      Use unstructured: partition_pdf(file_path, strategy="hi_res", 
        ocr_languages=["eng"], pdf_image_dpi=300)
      This internally uses pytesseract + poppler to rasterize pages then OCR them.
      Log: "Using OCR strategy for {filename} — this may take longer"
    
    For DOCX:
      Use unstructured: partition_docx(file_path)
    
    Each element returned as dict: {type: str, text: str, metadata: dict}
    Filter out empty elements (text.strip() == "")
    Return list of elements with their type labels (Title, NarrativeText, Table, ListItem)
    
    Add to each element's metadata: {"is_ocr": bool, "file_type": "pdf"|"docx"}
    
    Handle import gracefully: if unstructured not available, raise ImportError with install instructions.
    Handle OCR failure: if pytesseract not found, raise RuntimeError("OCR dependencies missing. 
      Run: brew install tesseract poppler (macOS) or apt-get install tesseract-ocr poppler-utils (Linux)")

services/ingestion/chunker.py:
  chunk_by_clause(elements: list[dict]) -> list[dict]:
    Track current section path as a stack of heading strings
    When element type == "Title" or starts with numbered pattern (r"^[IVX]+\.|^\d+\.|^Article"),
      update section_path stack
    Group NarrativeText elements under their current section_path
    Merge consecutive NarrativeText elements until hitting next heading or 1500 token limit
    Each chunk: {text: str, section_path: list[str], element_types: list[str]}
    Minimum chunk size: 100 characters (skip smaller)
    Return list of clause chunks

services/ingestion/extractor.py:
  extract_and_chunk(file_path: str, doc_type: str) -> list[dict]:
    Call parser.parse_document → elements
    Call chunker.chunk_by_clause → chunks
    Add page_number (from element metadata if available, else 0) and char_offset to each chunk
    Return enriched chunks
  
  clean_text(text: str) -> str:
    Remove control characters, normalize unicode, fix common PDF ligatures (ﬁ→fi, ﬂ→fl)
    Normalize multiple spaces and newlines

--- SECTION 2: NLP Services ---

NOTE: For NLP models, use lazy loading — initialize only on first use, not at import time.
Use a module-level singleton pattern with a None check.

services/nlp/ner.py:
  Class NERService (singleton):
    _model = None (class var)
    
    @classmethod
    def get_model(cls):
      If _model is None:
        Load from HuggingFace: pipeline("ner", model="nlpaueb/legal-bert-base-uncased",
          aggregation_strategy="simple", device=-1)  # CPU only for now
        Set cls._model
      Return cls._model
    
    @classmethod
    def extract_entities(cls, text: str) -> dict:
      Run model on text (truncate to 512 tokens if needed)
      Group results by entity type:
        ORG → parties, DATE → dates, MONEY → amounts, GPE/LOC → jurisdictions
      Return dict: {parties: list[str], dates: list[str], amounts: list[str], jurisdictions: list[str]}
      
      IMPORTANT: Wrap in try/except — if model fails, return empty dict with logged warning.
      Never crash the pipeline on NER failure.

services/nlp/classifier.py:
  Class ClauseClassifier (singleton):
    _model = None, _tokenizer = None (class vars)
    
    CUAD_LABELS: list of 20 most common clause types (use these for MVP):
      ["Indemnification", "Liability Cap", "IP Ownership", "Confidentiality/NDA",
       "Governing Law", "Dispute Resolution", "Termination for Convenience",
       "Termination for Cause", "Payment Terms", "Warranty", "Limitation of Liability",
       "Force Majeure", "Assignment", "Non-Compete/Non-Solicitation", 
       "Audit Rights", "Insurance", "Intellectual Property License", 
       "Change Order", "Scope of Work", "Representations & Warranties"]
    
    @classmethod
    def get_model(cls):
      Try to load: AutoTokenizer and AutoModelForSequenceClassification
        from "theatticusproject/cuad-roberta" (if available)
      If download fails (network timeout, model not found):
        Fall back to keyword-based classification (see below)
      
    @classmethod
    def classify(cls, text: str) -> tuple[str, float]:
      If model available: tokenize + forward pass → softmax → top label + confidence
      Fallback keyword classifier:
        Simple dict mapping keywords to clause types:
          {"indemnif": "Indemnification", "liability cap": "Liability Cap", 
           "intellectual property": "IP Ownership", "confidential": "Confidentiality/NDA",
           "governing law": "Governing Law", ...}
        Scan text.lower() for each keyword → return first match with confidence 0.7
        If no match: return ("unclassified", 0.0)

services/nlp/obligation.py:
  extract_obligations(text: str) -> list[dict]:
    Use spaCy (load en_core_web_sm for speed — not the transformer version here):
      Find sentences containing modal verbs: shall, must, agrees to, will, may, is required to
      For each modal sentence:
        Find the subject (nsubj of the modal or its head verb)
        Find the main action (verb + dobj/xcomp)
        Classify: is_mandatory = modal in ["shall", "must", "is required to"]
        Return {party: str, modal: str, action: str, is_mandatory: bool}
    Max 10 obligations per clause.
    Wrap in try/except — return [] on failure.

services/nlp/pipeline.py:
  process_clause(raw_clause: dict, org_id: str, document_id: str) -> dict:
    raw_text = raw_clause["text"]
    entities = NERService.extract_entities(raw_text)
    clause_type, confidence = ClauseClassifier.classify(raw_text)
    obligations = extract_obligations(raw_text)
    Return processed_clause dict with all fields (matches ProcessedClause model schema)
  
  process_document_nlp(raw_clauses: list[dict], org_id: str, document_id: str) -> list[dict]:
    Map process_clause over all raw_clauses
    Log progress every 10 clauses
    Return list of processed clause dicts

--- SECTION 3: Embedding Service ---

services/retrieval/embedder.py:
  Use sentence-transformers: SentenceTransformer("BAAI/bge-small-en-v1.5")  # small model, fast
  
  Class EmbeddingService (singleton):
    _model = None
    _qdrant = None
    COLLECTION_NAME = "contract_clauses"
    
    @classmethod
    def get_model(cls): lazy-load SentenceTransformer
    
    @classmethod
    def get_qdrant(cls): lazy-load QdrantClient from config QDRANT_URL
    
    @classmethod
    def ensure_collection_exists(cls):
      Check if collection "contract_clauses" exists in Qdrant
      If not: create with vector size=384 (bge-small output), distance=COSINE
    
    @classmethod
    def embed_and_upsert(cls, processed_clauses: list[dict], org_id: str) -> None:
      Texts = [c["raw_text"] for c in processed_clauses]
      Embeddings = cls.get_model().encode(texts, batch_size=32, show_progress_bar=False)
      
      Points = [PointStruct(
        id=str(uuid4()),  # store this as embedding_id back on the clause
        vector=embedding.tolist(),
        payload={org_id: org_id, clause_type: c["clause_type"], 
                 document_id: c["document_id"], clause_db_id: c["id"]}
      ) for embedding, c in zip(embeddings, processed_clauses)]
      
      Qdrant upsert in batches of 100.
      Return dict mapping clause_db_id → qdrant_point_id

--- SECTION 4: Celery Task ---

tasks/process_document.py:
  @celery.task(bind=True, max_retries=3)
  def process_document(self, document_id: str):
    
    Helper: update_document_status(db, document_id, status, progress_pct, error=None)
      Updates Document.status + stores progress in Redis key "job:{task_id}:progress"
    
    Step 1: Load document from DB. File is at Document.storage_path (local /tmp path).
            If likely_ocr=True in metadata_: log "⚠ OCR mode — processing may take 2-5 min"
    Step 2: update_document_status("ingesting", 10)
            Run extractor.extract_and_chunk(file_path, doc_type) → raw_clauses
            Log count: "{n} clause chunks extracted {'(OCR)' if is_ocr else ''}"
            Bulk insert RawClause records to DB
            update_document_status("ingesting", 30)
    Step 3: update_document_status("nlp_processing", 35)
            Run pipeline.process_document_nlp(raw_clauses, org_id, document_id) → processed
            Bulk insert ProcessedClause records to DB
            update_document_status("nlp_processing", 65)
    Step 4: EmbeddingService.embed_and_upsert(processed, org_id)
            Update each ProcessedClause.embedding_id in DB
            update_document_status("nlp_processing", 80)
    Step 5: update_document_status("complete", 100)
            Log: "✓ Document {doc_id} processed. {n} clauses indexed. Admin must manually trigger playbook regeneration."
            DO NOT auto-call regenerate_playbook — admin controls when playbook is rebuilt.
    
    On any exception: update_document_status("error", 0, error=str(e)), raise self.retry(exc=e)
  
  Store job metadata in Redis: "job:{task_id}" = {stage, progress_pct, document_id, org_id}
  TTL: 24 hours

--- SECTION 5: API Routes ---

api/routes/documents.py:
  All routes use get_org_id(request) for org scoping. No auth checks (deferred).
  # TODO: replace get_org_id with real auth when auth is implemented
  
  POST /api/documents/upload (multipart/form-data):
    Fields: file (UploadFile), doc_type (str)
    org_id = get_org_id(request)
    1. Validate file type (PDF/DOCX only), size (max 50MB)
    2. Detect if PDF is likely scanned: check file size vs page count heuristic
       Store metadata_: {"likely_ocr": bool} on the Document record
    3. Save file to local /tmp/{org_id}/{doc_id}/{filename} (no cloud storage yet — deferred with auth)
    4. Insert Document record to DB with storage_path = local path
    5. Enqueue: task = process_document.delay(str(doc_id))
    6. Store job metadata to Redis: {stage: "queued", progress_pct: 0, document_id, org_id}
    7. Return DocumentUploadResponse
  
  GET /api/documents/ — list org documents:
    org_id = get_org_id(request)
    Query DB for org's non-deleted documents, ordered by upload_date desc
    Return list[DocumentListItem]
  
  DELETE /api/documents/{doc_id}:
    org_id = get_org_id(request)
    Soft delete (is_deleted = True)
    DO NOT auto-trigger playbook regeneration — admin must do this manually
    Return {"message": "deleted", "note": "Regenerate the playbook from the Playbook page to reflect this removal"}
  
  GET /api/documents/{doc_id}/retry:
    org_id = get_org_id(request)
    Load document, verify org_id matches
    If status != "error": return 400 "Document is not in error state"
    Reset status to "pending", re-enqueue process_document.delay(doc_id)
    Return {"message": "requeued", "job_id": new_task_id}

api/routes/pipeline.py:
  GET /api/pipeline/status/{job_id}:
    Pull from Redis key "job:{job_id}"
    Also check Celery AsyncResult as fallback
    Return PipelineStatusResponse

--- SECTION 6: Commit ---

git add -A && git commit -m "feat: ingestion + NLP pipeline — parser, chunker, NER, classifier, obligations, embedder, Celery task"
```

---

## Workflow 3 — Distillation + Content Generation

**Branch**: `workflow-3/distillation-generation`
**Owns**: `backend/app/services/distillation/`, `backend/app/services/generation/`, `backend/app/tasks/regenerate_playbook.py`, `backend/app/tasks/generate_onboarding.py`, `backend/app/api/routes/playbook.py`, `backend/app/api/routes/onboarding.py`, `backend/app/services/export/`

---

**Claude Code Prompt:**

```
Continue building LexOnboard. Workflows 1 and 2 are complete. Now build the Claude API distillation service, content generation (textbook, quizzes, checklist), export, and their API routes.

The Anthropic SDK is installed. Import: from anthropic import Anthropic. 
Client: client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
Model: "claude-sonnet-4-20250514"

--- SECTION 1: Distillation Service ---

services/distillation/prompts.py:
  SYNTHESIS_SYSTEM_PROMPT = """
  You are a legal knowledge engineer specializing in extracting institutional knowledge from 
  corporate contracts. You receive multiple examples of the same clause type from a company's 
  actual signed contracts. Your job is to identify patterns that represent this organization's 
  real practices and positions.

  Return ONLY valid JSON. No preamble, no markdown fences, no explanation outside the JSON.
  """

  SYNTHESIS_USER_TEMPLATE = """
  Clause type: {clause_type}
  
  Here are {n_clauses} examples of this clause type from this organization's contracts:
  
  {clauses_text}
  
  Extract and return this JSON structure:
  {{
    "clause_type": "{clause_type}",
    "title": "<human-friendly section title>",
    "non_negotiables": ["<absolute requirement 1>", "<absolute requirement 2>"],
    "standard_positions": [
      {{"description": "...", "acceptable_range": "...", "rationale": "..."}}
    ],
    "red_flags": ["<pattern that should trigger escalation 1>", ...],
    "industry_baseline": "<what is typical in this sector for this clause type>",
    "example_clauses": ["<sanitized example clause text 1>", "<sanitized example clause text 2>"]
  }}
  
  Base everything strictly on the provided examples. Do not invent positions not evidenced in the text.
  """

services/distillation/synthesizer.py:
  synthesize_clause_type(clause_type: str, clauses: list[ProcessedClause]) -> dict | None:
    If len(clauses) == 0: return None
    Cap at 20 clauses (take first 20 to stay in token budget)
    
    clauses_text = "\n\n---\n\n".join([
      f"[Clause {i+1}]\n{c.raw_text}" for i, c in enumerate(clauses[:20])
    ])
    
    Call Claude API:
      messages = [{"role": "user", "content": SYNTHESIS_USER_TEMPLATE.format(...)}]
      system = SYNTHESIS_SYSTEM_PROMPT
      max_tokens = 2000
      temperature = 0 (deterministic output for JSON)
    
    Parse response: json.loads(response.content[0].text)
    On JSONDecodeError: retry once with temperature=0, added user message "Respond with ONLY the JSON object."
    On second failure: log error, return None
    Return parsed dict

services/distillation/merger.py:
  merge_into_playbook(org_id: str, sections: list[dict], doc_count: int) -> dict:
    Filter out None sections
    Sort sections by a predefined display order (Parties first, Scope, Time, Payment, Liability, IP, Termination, Governing Law, Other)
    Return OrgPlaybook dict ready for DB insertion:
      {org_id, version: (current_version + 1), is_current: True, sections, doc_count,
       generated_at: now(), onboarding_ready: False}

tasks/regenerate_playbook.py:
  @celery.task
  def regenerate_playbook(org_id: str):
    1. Load all ProcessedClause records for org_id from DB
    2. Group by clause_type
    3. For each clause_type with >= 2 clauses:
         section = synthesize_clause_type(clause_type, clauses)
       Collect non-None sections
    4. If no sections generated: log warning + return
    5. Set current OrgPlaybook.is_current = False for this org
    6. Create new OrgPlaybook with merged sections
    7. Enqueue generate_onboarding.delay(org_id, new_playbook_id)
    8. Log: "Playbook v{version} generated with {n} sections from {doc_count} docs"

--- SECTION 2: Generation Services ---

services/generation/prompts.py:
  TEXTBOOK_SYSTEM_PROMPT = """
  You are a legal training writer creating onboarding materials for non-specialist professionals 
  (paralegals, project managers, junior in-house counsel) joining a specific company. 
  Your writing is clear, practical, and grounded in how THIS organization actually operates — 
  not generic legal theory. Use plain English. Avoid jargon where possible; define it when necessary.
  """

  TEXTBOOK_CHAPTER_TEMPLATE = """
  You are writing Chapter {chapter_num} of an onboarding guide for new hires at this company.
  
  Chapter topic: {clause_type} — {section_title}
  
  This company's actual positions on this topic:
  {playbook_section_json}
  
  Write a chapter of approximately 400-600 words covering:
  1. What this clause type is and why it matters (2-3 sentences, very plain language)
  2. How THIS company handles it (reference the non-negotiables and standard positions directly)
  3. What to watch out for (the red flags, explained with examples)
  4. A practical tip for when you're reviewing a contract
  
  End with exactly 3 key takeaways formatted as:
  KEY_TAKEAWAYS:
  - <takeaway 1>
  - <takeaway 2>
  - <takeaway 3>
  
  Write for someone who studied business, not law.
  """

  QUIZ_GENERATION_TEMPLATE = """
  Generate a quiz for Chapter {chapter_num}: {section_title}
  
  Based on this chapter content:
  {chapter_content}
  
  And this org's actual clause examples:
  {example_clauses}
  
  Generate exactly 4 questions in this JSON format:
  [
    {{
      "question_type": "mcq",
      "text": "<question>",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "correct_answer": "A",
      "explanation": "<why this is correct and why others are wrong>",
      "clause_type": "{clause_type}"
    }},
    {{
      "question_type": "true_false",
      "text": "<statement>",
      "correct_answer": "True" or "False",
      "explanation": "<explanation>",
      "clause_type": "{clause_type}"
    }},
    {{
      "question_type": "scenario",
      "text": "You are reviewing a contract and see the following clause:",
      "context": "<use a real example clause from the org's contracts, lightly sanitized>",
      "options": ["A. Approve — this is standard", "B. Flag for review — this deviates from our position", "C. Reject — this is a non-negotiable violation", "D. Skip — this clause type doesn't apply"],
      "correct_answer": "B" or "C" (based on playbook),
      "explanation": "<explain the correct action and why>",
      "clause_type": "{clause_type}"
    }},
    {{
      "question_type": "mcq",
      "text": "<another question>",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "correct_answer": "<letter>",
      "explanation": "<explanation>",
      "clause_type": "{clause_type}"
    }}
  ]
  Return ONLY the JSON array.
  """

  CHECKLIST_GENERATION_PROMPT = """
  You are generating a contract review checklist for a company's new hires.
  
  Based on this company's contract playbook:
  {playbook_json}
  
  Generate a comprehensive contract review checklist in this exact JSON structure:
  {{
    "categories": [
      {{
        "name": "I. Tender Submission & Execution Preliminaries",
        "subcategories": [
          {{
            "name": "A. Documents & Dates",
            "items": [
              {{
                "item_clause": "Tender/Contract Name",
                "review_question": "Is the official name or title noted and correct?",
                "is_non_negotiable": false,
                "clause_type": "Scope of Work"
              }}
            ]
          }}
        ]
      }}
    ]
  }}
  
  Cover these categories minimum: Submission & Execution, Parties & Authority, Scope & Deliverables, 
  Time & Delays, Payment & Financial, Liability & Risk, IP & Confidentiality, Termination, 
  Governing Law. Mark is_non_negotiable: true for items that correspond to this org's non-negotiables.
  Include 5-8 items per subcategory. Return ONLY valid JSON.
  """

services/generation/textbook.py:
  generate_textbook(playbook: OrgPlaybook) -> dict:
    chapters = []
    
    Chapter 0: Introduction (hardcoded template, no Claude call needed):
      Title: "Welcome to [org name]'s Contract Framework"
      Content: Explain what this guide covers, how to use it, what the org does
    
    For each section in playbook.sections (up to 8 sections for page budget):
      Call Claude API with TEXTBOOK_CHAPTER_TEMPLATE
      Parse response: split on "KEY_TAKEAWAYS:" to extract chapter body + takeaways
      Append to chapters list
    
    Final chapter: "Red Flags Summary" — hardcoded aggregation of all red_flags across sections
    
    Return {chapters: list, page_estimate: estimate_pages(chapters)}
  
  estimate_pages(chapters: list) -> int:
    Total words = sum of word count across all chapter content
    1 page ≈ 350 words → return min(20, max(10, total_words // 350))

services/generation/quiz.py:
  generate_quiz_for_chapter(chapter: dict, playbook_section: dict) -> dict:
    Call Claude API with QUIZ_GENERATION_TEMPLATE
    Parse JSON array response
    Add id (uuid4) to each question
    Return {quiz_type: "chapter_review", questions: parsed, chapter_index: chapter["chapter_number"]}
  
  generate_final_assessment(all_sections: list[dict]) -> dict:
    Select 2 questions from each of the 5 most important clause types
    Shuffle and return 10-question final assessment
    quiz_type: "final_assessment"

services/generation/checklist.py:
  generate_checklist(playbook: OrgPlaybook) -> dict:
    Prepare playbook_json: summarized version of playbook (only non_negotiables + clause types)
    Call Claude API with CHECKLIST_GENERATION_PROMPT, max_tokens=4000
    Parse JSON response
    Validate structure: must have at least 3 categories
    Return parsed dict

tasks/generate_onboarding.py:
  @celery.task
  def generate_onboarding(org_id: str, playbook_id: str):
    1. Load OrgPlaybook from DB
    2. Generate textbook → insert TextbookContent record
    3. For each chapter in textbook: generate quiz → insert QuizSet record
    4. Generate final assessment → insert QuizSet (quiz_type="final_assessment")
    5. Generate checklist → insert ContractChecklist record
    6. Update OrgPlaybook.onboarding_ready = True
    7. Log: "Onboarding content generated for org {org_id}"

--- SECTION 3: Export Services ---

services/export/word_exporter.py:
  export_playbook_to_docx(playbook: OrgPlaybook, org_name: str) -> bytes:
    Use python-docx. Create Document() with:
    
    Style: Title page with org name + "Contract Standards Playbook" + version + date
    
    Table of Contents section (manual — list section titles)
    
    For each PlaybookSection:
      Heading 1: section.title
      
      Heading 2: "Non-Negotiables"
      Bulleted list: each non_negotiable with red font color (RGBColor(0xC0, 0x00, 0x00))
      
      Heading 2: "Standard Positions"
      For each standard_position: table with 3 columns (Description | Acceptable Range | Rationale)
      
      Heading 2: "Red Flags"
      Bulleted list: each red_flag with orange font color
      
      Heading 2: "Industry Baseline"
      Normal paragraph
      
      Page break between sections
    
    Save to BytesIO buffer, return buffer.getvalue()

services/export/pdf_exporter.py:
  export_playbook_to_pdf(playbook: OrgPlaybook, org_name: str) -> bytes:
    Use fpdf2. Clean, professional layout:
    
    Title page with large title + org name + date + "CONFIDENTIAL — INTERNAL USE ONLY"
    
    For each section: heading, then sub-sections with consistent spacing
    Non-negotiables: red bullets
    Red flags: orange bullets
    
    Footer: page numbers + org name
    Save to BytesIO buffer, return buffer.getvalue()

--- SECTION 4: API Routes ---

api/routes/playbook.py:
  All routes use get_org_id(request). No auth checks (deferred).
  # TODO: replace get_org_id with real auth when auth is implemented
  
  GET /api/playbook/current:
    org_id = get_org_id(request)
    Return current OrgPlaybook as OrgPlaybookResponse
    If none exists: return 404 with message "No playbook generated yet. Upload documents and trigger regeneration."
  
  GET /api/playbook/versions:
    org_id = get_org_id(request)
    Return list of all OrgPlaybook versions for org (id, version, generated_at, doc_count, is_current)
  
  POST /api/playbook/regenerate:
    org_id = get_org_id(request)
    CHECK: are there any documents with status="complete" for this org?
    If no complete documents: return 400 "No processed documents found. Upload and process documents first."
    Enqueue regenerate_playbook.delay(org_id)
    Store regeneration job in Redis: "playbook_regen:{org_id}" = {stage: "queued", started_at}
    Return {"message": "Playbook regeneration started", "job_id": task_id}
    NOTE: This is the ONLY way to trigger playbook regeneration. It is never triggered automatically.
  
  GET /api/playbook/regenerate/status:
    org_id = get_org_id(request)
    Pull from Redis "playbook_regen:{org_id}"
    Return {stage, started_at, completed_at (nullable)}
  
  POST /api/playbook/export:
    org_id = get_org_id(request)
    Body: ExportRequest {format: "docx" | "pdf"}
    1. Load current playbook from DB
    2. Generate file bytes from appropriate exporter
    3. Save to local /tmp/exports/{org_id}/playbook_v{version}.{ext}
    4. Return as FileResponse (direct download, no cloud storage yet)
  
  PATCH /api/playbook/sections/{clause_type}:
    org_id = get_org_id(request)
    Body: partial PlaybookSectionSchema
    1. Load current playbook
    2. Find matching section by clause_type
    3. Apply edits (merge, don't replace)
    4. Save PlaybookEdit record to DB
    5. Return updated section

api/routes/onboarding.py:
  All routes use get_org_id(request) + get_user_context(request). No auth checks (deferred).
  
  GET /api/onboarding/textbook:
    Load TextbookContent for org's current playbook
    Return TextbookResponse
  
  GET /api/onboarding/quizzes:
    Load all QuizSets for org's current playbook (ordered by chapter_index)
    Return list[QuizSetResponse]
  
  GET /api/onboarding/checklist:
    Load ContractChecklist for org's current playbook
    Return ContractChecklistResponse
  
  GET /api/onboarding/progress:
    user_id = get_user_context(request)["user_id"]
    Load OnboardingProgress for user_id (create if not exists)
    
    Quiz pass threshold: 100% (all questions must be correct to count as "passed")
    quizzes_passed = count of quiz_ids where quiz_scores[quiz_id] == 1.0
    
    completion_percentage:
      textbook_pct = len(chapters_read) / total_chapters
      quiz_pct = quizzes_passed / total_quizzes
      return (textbook_pct * 0.5) + (quiz_pct * 0.5) * 100
    
    Return OnboardingProgressResponse
  
  PATCH /api/onboarding/progress:
    user_id = get_user_context(request)["user_id"]
    Accept OnboardingProgressUpdate
    For quiz_score updates: score must be 1.0 (100%) to mark quiz as completed
    Upsert OnboardingProgress for user_id
    Return updated OnboardingProgressResponse

--- SECTION 5: Commit ---

git add -A && git commit -m "feat: distillation + generation — Claude API synthesis, textbook, quizzes, checklist, export, routes"
```

---

## Workflow 4 — RAG Chat Service

**Branch**: `workflow-4/rag-chat`
**Owns**: `backend/app/services/retrieval/retriever.py`, `backend/app/services/retrieval/chat_service.py`, `backend/app/api/routes/chat.py`

---

**Claude Code Prompt:**

```
Continue building LexOnboard. Workflows 1-3 are complete. Now build the RAG chat service — the "ask the playbook" feature that lets new hires query the org's contract knowledge.

--- SECTION 1: Retriever ---

services/retrieval/retriever.py:
  retrieve_relevant_clauses(question: str, org_id: str, top_k: int = 5) -> list[dict]:
    1. Embed question using EmbeddingService (same singleton from embedder.py)
    2. Query Qdrant "contract_clauses" collection:
       - vector = question_embedding
       - limit = top_k
       - with_payload = True
       - filter = Filter(must=[FieldCondition(key="org_id", match=MatchValue(value=org_id))])
    3. For each hit:
       - Load full ProcessedClause from PostgreSQL using hit.payload["clause_db_id"]
       - Build result dict: {id, clause_type, section_path, raw_text, score: hit.score}
    4. Return sorted by score desc

--- SECTION 2: Chat Service ---

services/retrieval/chat_service.py:
  CHAT_SYSTEM_PROMPT = """
  You are a legal knowledge assistant for a specific organization. You have access to this 
  organization's actual contract history, distilled into a knowledge base. When answering 
  questions from new hires, you:
  
  1. Ground every answer in the retrieved contract clauses provided to you
  2. Cite your sources: reference the clause type and section when stating a position
  3. Distinguish clearly between: (a) this org's non-negotiables, (b) their standard positions, 
     (c) acceptable variations, and (d) general legal practice
  4. If the retrieved clauses don't cover the question, say so — don't invent positions
  5. Keep answers practical: what should this person actually DO with this information?
  
  You are NOT a licensed attorney and this is NOT legal advice. You are explaining how this 
  organization has historically handled contract matters based on their actual documents.
  """

  answer_question(
    question: str,
    org_id: str,
    conversation_history: list[dict],
    session_id: str
  ) -> dict:
    
    1. Retrieve top-5 relevant clauses: retrieve_relevant_clauses(question, org_id, top_k=5)
    
    2. Build context block:
       context = "\n\n".join([
         f"[Source {i+1}: {c['clause_type']} — {' > '.join(c['section_path'])}]\n{c['raw_text']}"
         for i, c in enumerate(retrieved)
       ])
    
    3. Build messages array:
       - System: CHAT_SYSTEM_PROMPT
       - Include last 4 turns from conversation_history (2 user + 2 assistant)
       - User message: f"Based on our organization's contract clauses:\n\n{context}\n\nQuestion: {question}"
    
    4. Call Claude API (NON-STREAMING for now — streaming in Phase 2):
       max_tokens = 1500
       temperature = 0.3
    
    5. Parse response text
    
    6. Persist ChatMessage records (user + assistant) to DB
    
    7. Return:
       {
         answer: response_text,
         sources: [{id, clause_type, section_path, excerpt: raw_text[:200] + "..."}],
         session_id: session_id
       }

--- SECTION 3: API Route ---

api/routes/chat.py:
  POST /api/chat/query (authenticated):
    Body: ChatQueryRequest {question, session_id, conversation_history}
    
    Validate: question must be non-empty, max 500 chars
    Validate: conversation_history max 10 turns
    
    Call chat_service.answer_question(...)
    
    Increment OnboardingProgress.chat_queries by 1 for this user
    
    Return ChatResponse
  
  GET /api/chat/history (authenticated):
    session_id query param
    Return list of ChatMessage for this session (user's own messages only, scoped to org)

--- SECTION 4: Commit ---

git add -A && git commit -m "feat: RAG chat — retriever, chat service, Claude API QA, history"
```

---

## Workflow 5 — Frontend Foundation + Auth

**Branch**: `workflow-5/frontend-foundation`
**Owns**: `frontend/src/app/(auth)/`, `frontend/src/lib/`, `frontend/src/types/`, `frontend/src/app/layout.tsx`, `frontend/src/components/ui/`

---

**Claude Code Prompt:**

```
Build the frontend foundation for LexOnboard, an AI-powered legal contract onboarding platform.

Stack: Next.js 14 (App Router), TypeScript, Tailwind CSS, Supabase for auth.

Design direction: Legal-professional aesthetic with a modern edge. NOT sterile corporate gray.
Palette: Deep navy (#0F1729) backgrounds, off-white (#F5F3EE) text, gold accent (#C9A84C) for 
emphasis, warm slate (#64748B) for secondary. Typography: "Playfair Display" for headings 
(serious, authoritative), "DM Sans" for body (readable, modern). 
Load fonts from Google Fonts in layout.tsx.

The UI should feel like a premium tool built for professionals who respect their work — 
think Bloomberg Terminal meets modern SaaS. Dark mode first.

--- SECTION 1: Core Setup ---

frontend/src/lib/api.ts:
  Base URL: process.env.NEXT_PUBLIC_API_URL (defaults to http://localhost:8000)
  
  DEV_ORG_ID: process.env.NEXT_PUBLIC_DEV_ORG_ID || "dev-org-001"
  DEV_USER_ID: process.env.NEXT_PUBLIC_DEV_USER_ID || "dev-user-001"  
  DEV_USER_ROLE: process.env.NEXT_PUBLIC_DEV_USER_ROLE || "admin"  ← change to "new_hire" to test that view
  
  api object with typed methods:
    get<T>(path: string): Promise<T>
    post<T>(path: string, body?: unknown): Promise<T>
    patch<T>(path: string, body?: unknown): Promise<T>
    delete<T>(path: string): Promise<T>
    upload<T>(path: string, formData: FormData): Promise<T>
  
  All methods automatically include headers:
    "X-Org-ID": DEV_ORG_ID
    "X-User-ID": DEV_USER_ID
    "X-User-Role": DEV_USER_ROLE
    "Content-Type": "application/json" (except upload which uses FormData)
  
  On non-2xx response: throw typed ApiError with { status, message }
  
  # TODO: replace DEV_* headers with real auth token when auth is implemented

frontend/src/lib/context.ts:
  DevContext — simple React context holding the current dev user state:
    { orgId, userId, role, setRole }
  
  DevContextProvider: wraps the app, reads from env vars initially
  useDevContext() hook: returns current context values
  
  This lets us switch between "admin" and "new_hire" views in dev without auth.
  Add a role-switcher button in the sidebar footer (dev only, hidden when NODE_ENV=production).

frontend/src/types/index.ts:
  Export TypeScript interfaces matching backend Pydantic schemas:
    Document, DocumentListItem, PipelineStatus, OrgPlaybook, PlaybookSection,
    TextbookContent, TextbookChapter, QuizSet, Question, ContractChecklist,
    OnboardingProgress, ChatMessage, ChatResponse, SourceClause

frontend/src/app/layout.tsx:
  Load Playfair Display (weights 400, 600) + DM Sans (weights 400, 500, 600) from Google Fonts
  Apply dark background: bg-[#0F1729] text-[#F5F3EE]
  Include Toaster from sonner for notifications
  Wrap with DevContextProvider
  Apply font CSS variables

--- SECTION 2: Dev Landing + Role Selector ---

Since auth is deferred, the app opens directly to the dashboard.
No login page needed. Instead:

frontend/src/app/page.tsx:
  Redirect to /dashboard (using Next.js redirect())

frontend/src/app/dashboard/layout.tsx:
  Side-by-side: <Sidebar /> + main content area (flex-1, overflow-y-auto, p-8)
  If role === "new_hire": sidebar shows onboarding nav; redirect /dashboard → /onboarding
  If role === "admin" or "lawyer": sidebar shows admin nav

--- SECTION 3: Navigation Shell ---

frontend/src/components/shell/Sidebar.tsx:
  Fixed left sidebar (240px wide) on dark navy background
  Logo at top: "LexOnboard" gold wordmark
  
  Navigation sections based on role from useDevContext():
    Admin/lawyer role:
      - Dashboard (grid icon) → /dashboard
      - Documents (upload icon) → /dashboard/upload
      - Playbook (book icon) → /dashboard/playbook
      - Settings (gear icon) → /dashboard/settings
    New hire role:
      - My Onboarding (home icon) → /onboarding
      - Textbook (book-open icon) → /onboarding/textbook
      - Quizzes (check-circle icon) → /onboarding/quiz
      - Contract Checklist (list icon) → /onboarding/checklist
      - Ask the Playbook (message-square icon) → /onboarding/chat
  
  Active state: gold left border + slightly lighter background
  
  Bottom of sidebar — dev only (process.env.NODE_ENV === 'development'):
    Role switcher: two small buttons "Admin view" / "New Hire view"
    Clicking switches DEV_USER_ROLE in DevContext and updates api.ts headers
    Small "DEV MODE" badge above buttons in orange so it's obvious
  
  Use lucide-react for all icons.

--- SECTION 4: Commit ---

git add -A && git commit -m "feat: frontend foundation — no-auth dev context, layout, sidebar, API client, types"
```

---

## Workflow 6 — Dashboard + Upload + Pipeline UI

**Branch**: `workflow-6/dashboard-upload`
**Owns**: `frontend/src/app/dashboard/page.tsx`, `frontend/src/app/dashboard/upload/page.tsx`, `frontend/src/components/upload/`, `frontend/src/components/pipeline/`

---

**Claude Code Prompt:**

```
Continue building the LexOnboard frontend. Auth, layout, and sidebar are done. Build the admin dashboard, document upload flow, and pipeline progress UI.

Design: maintain the dark navy (#0F1729) + gold (#C9A84C) + Playfair/DM Sans design system.

--- SECTION 1: Document Upload ---

components/upload/DropZone.tsx:
  react-dropzone based component
  Accepts: application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document
  Max size: 50MB
  
  Visual states:
    Idle: dashed border, centered icon + "Drop contracts here or click to browse"
           Subtitle: "PDF and DOCX up to 50MB"
    Drag-over: gold border glow, background lightens slightly
    Uploading: progress bar with filename
  
  On drop: callback with File[]
  Show file size in KB/MB next to filename
  Show file type badge (PDF / DOCX)

components/upload/DocTypeSelector.tsx:
  Dropdown to select doc_type before upload
  Options: Master Agreement, Compliance Document, NDA, Statement of Work, Other
  Required field — upload button disabled until selected

components/upload/DocumentCard.tsx:
  Card showing: filename (truncated), doc_type badge, upload_date relative ("2 days ago"),
  status badge (color-coded: pending=gray, nlp_processing=blue, distilling=purple, complete=green, error=red)
  Delete button (trash icon) — confirm dialog before delete

frontend/src/app/dashboard/upload/page.tsx:
  Page title: "Upload Documents" (Playfair Display, h1)
  Subtitle: "Add master agreements and compliance documents to build your org's knowledge base"
  
  DropZone component
  DocTypeSelector below it (shown after file selected)
  "Upload & Process" button — calls POST /api/documents/upload
  
  After upload success: show PipelineStatus component for the returned job_id
  On error: sonner toast with error message

--- SECTION 2: Pipeline Progress ---

components/pipeline/StageIndicator.tsx:
  Horizontal stepper showing stages: Uploading → Parsing → NLP Analysis → Distilling → Ready
  
  Stage states:
    completed: gold checkmark circle
    active: spinning loader in gold
    pending: hollow gray circle
  
  Connecting lines between stages (gray → gold as stages complete)

components/pipeline/PipelineStatus.tsx:
  Props: job_id, document_id, onComplete callback
  
  Polls GET /api/pipeline/status/{job_id} every 3 seconds using setInterval
  Shows StageIndicator with current stage highlighted
  Shows percentage: "67% complete"
  
  On complete: call onComplete(), show success toast "Document processed — playbook updated"
  On error: show error message + "Contact support" link
  Stop polling on unmount (cleanup in useEffect return)

--- SECTION 3: Admin Dashboard ---

frontend/src/app/dashboard/page.tsx:
  Stats row at top (3 cards):
    - Documents Processed: count from API
    - Playbook Version: current version number
    - Team Members: count of users in org
  
  Cards: dark background (#1A2540), subtle border, number in large Playfair Display
  
  Recent Documents section:
    Table: Filename | Type | Uploaded | Status | Actions
    Pagination: 10 per page
    Status badges color-coded
    Actions: Delete (with confirm dialog)
  
  "Upload New Documents" button → links to /dashboard/upload
  
  If no documents yet: empty state with illustration-like ASCII art box:
    "No documents yet. Upload your first contract to get started."
    Large upload button centered

--- SECTION 4: Playbook Viewer ---

frontend/src/app/dashboard/playbook/page.tsx:
  Left sidebar (220px): section navigation list (clause type links)
  Main content: PlaybookViewer component
  Right panel (180px): metadata (version, date, doc count) + export buttons

components/playbook/PlaybookViewer.tsx:
  Fetch GET /api/playbook/current on mount
  
  Loading state: skeleton cards
  Empty state: "Playbook generating..." if documents exist but onboarding_ready=false
  
  For each PlaybookSection:
    Section heading (Playfair Display)
    
    "Non-Negotiables" subsection:
      Red-bordered card, warning icon
      Bulleted list with red dot
    
    "Standard Positions" subsection:
      For each position: expandable card (title shown, click to expand for full detail)
    
    "Red Flags" subsection:
      Orange-bordered card, alert triangle icon
      Bulleted list with orange dot
    
    "Industry Baseline":
      Gray info card, italic text
    
    Divider between sections

components/playbook/ExportButton.tsx:
  Two buttons: "Export as Word" and "Export as PDF"
  On click: POST /api/playbook/export → poll for URL → window.open(url) for download
  Loading state: spinner in button

--- SECTION 5: Commit ---

git add -A && git commit -m "feat: dashboard, upload flow, pipeline status, playbook viewer"
```

---

## Workflow 7 — New Hire Onboarding UI

**Branch**: `workflow-7/onboarding-ui`
**Owns**: `frontend/src/app/onboarding/`, `frontend/src/components/onboarding/`

---

**Claude Code Prompt:**

```
Continue building LexOnboard. Build the complete new hire onboarding UI — textbook reader, interactive quizzes, contract checklist, and RAG chat.

Maintain the dark navy + gold + Playfair/DM Sans design system. The onboarding UI should feel like a premium learning platform — think Brilliant.org level of polish for professional training.

--- SECTION 1: Textbook Reader ---

components/onboarding/TextbookReader.tsx:
  Left sidebar: chapter list with completion checkmarks
    Each chapter: number + title, checkmark if read
    Currently viewing: gold left border highlight
  
  Main reading area (max-width 720px, centered):
    Chapter number: small gold uppercase label ("CHAPTER 3")
    Chapter title: Playfair Display, large
    Content: render markdown using a simple markdown renderer 
      (handle ##, ###, **bold**, *italic*, bullet lists — no need for full MDX)
    
    "Key Takeaways" box at bottom of each chapter:
      Gold-bordered box
      3 bullet points
      Slightly warmer background
    
    Progress through chapter: scroll-based — mark chapter as read when user scrolls to 75% of chapter
    
    Navigation: "← Previous Chapter" and "Next Chapter →" buttons at bottom
    On chapter complete: PATCH /api/onboarding/progress with chapter index
  
  Reading progress bar at very top: thin gold line filling across screen

components/onboarding/ProgressRing.tsx:
  Circular SVG progress ring
  Props: percentage (0-100), label, size
  Gold stroke on dark navy background
  Center: large percentage number

frontend/src/app/onboarding/textbook/page.tsx:
  Full-width layout with TextbookReader
  Fetch GET /api/onboarding/textbook on mount

--- SECTION 2: Interactive Quizzes ---

components/onboarding/QuizCard.tsx:
  Shows one question at a time.
  
  Header: quiz type badge + question number / total
  
  Question text: large, clear
  
  Scenario type: show "context" block in styled code-like box (monospace, slightly lighter bg)
  
  MCQ: 4 option buttons (A/B/C/D)
    Default: dark card buttons with letter badge
    After answer: 
      Correct = green border + checkmark
      Incorrect = red border + X
      Correct answer highlighted if user was wrong
  
  True/False: two large buttons side by side
  
  Explanation box (shown after answer):
    Slides down with animation
    Icon: lightbulb
    Explanation text in slightly gold-tinted background
  
  "Next Question →" button appears after explanation shown
  
  Disable all options after selection (no changing answers)

components/onboarding/QuizResults.tsx:
  Score: large number "8/10" in Playfair Display
  
  Pass/Fail logic — 100% is the only passing score (mastery, not a grade):
    10/10 = PASSED — green badge + checkmark: "Chapter mastered. Onboarding credit earned."
    Anything less = NOT YET — amber badge: "You need 100% to complete this chapter."
    No partial credit messaging. No "Good try!" — this is legal training.
  
  Per-question summary:
    Checkmark or X per question
    Click to expand: show question + your answer + correct answer + explanation
  
  Buttons:
    If passed: "Next Chapter →" (prominent gold)
    If failed: "Retry Quiz" (reshuffles questions, primary) + "Back to Chapter" (secondary, to re-read)
    Failed state shows: "Review the chapter, then retake. You can retry as many times as needed."
  
  POST quiz score to /api/onboarding/progress on completion
  Only POST with completed=true if score === 1.0 (all correct)

frontend/src/app/onboarding/quiz/[id]/page.tsx:
  Fetch specific QuizSet by id from GET /api/onboarding/quizzes
  State machine: "intro" → "question" → "results"
  Intro: quiz title, question count, estimated time (n questions × 1 min)
  Run through QuizCard for each question
  Show QuizResults at end

--- SECTION 3: Contract Checklist ---

components/onboarding/ChecklistTool.tsx:
  Renders the ContractChecklist as an interactive table — closely matching the image provided.
  
  Table structure:
    Columns: [checkbox] | Category | Item / Clause | Check Point / Review Question
    
    Category rows: merged cell with category name, light separator background
    Subcategory rows: subcategory name spans full row with subtle italic style
    Item rows: checkbox + item_clause + review_question
    
    Non-negotiable items: thin red left border on the row, red dot in category cell
    
    Completed items: gray out the row (opacity 60%), checkmark turns gold
  
  Session state: checked items stored in useState (not persisted — checklist is reusable)
  
  Progress: "12 of 34 items checked" counter in header
  
  "Export Checklist (PDF)" button: 
    Opens browser print dialog with print-specific CSS that hides sidebar/buttons
    Print CSS: white background, black text, proper table formatting
  
  "Reset" button: clear all checkboxes with confirmation

frontend/src/app/onboarding/checklist/page.tsx:
  Page title: "Contract Review Checklist"
  Subtitle: "Use this checklist every time you review a new contract"
  Fetch GET /api/onboarding/checklist
  Render ChecklistTool

--- SECTION 4: RAG Chat Interface ---

components/onboarding/ChatInterface.tsx:
  Full-height layout (viewport height minus header):
  
  Left panel (invisible on mobile): "Suggested Questions"
    Static list of 5 suggested questions (hardcoded, good starting points):
    - "What are our non-negotiables on indemnification?"
    - "What's our standard position on governing law?"
    - "What should I flag in a termination clause?"
    - "What's the typical liability cap structure we use?"
    - "What IP ownership terms do we always insist on?"
    Click to send as message
  
  Main chat area:
    Message bubbles:
      User: right-aligned, gold background, dark text
      Assistant: left-aligned, dark card background
    
    Source clause cards below each assistant message:
      Small cards showing: clause_type badge + first 120 chars of excerpt
      Click to expand full text in a slide-out panel
    
    Loading state: three animated dots bubble (while waiting for response)
  
  Input area:
    Text input (full width, dark background)
    Send button (gold, arrow icon)
    "Powered by your organization's contract history" fine print
  
  Conversation management:
    sessionId: generate uuid4 on component mount, persist in sessionStorage
    conversation_history: keep last 8 messages in state
    POST /api/chat/query on send
    Scroll to bottom on new message

frontend/src/app/onboarding/chat/page.tsx:
  Full screen layout (no padding wasting space)
  Fetch suggested questions from static list (no API needed)
  Render ChatInterface

--- SECTION 5: Onboarding Home ---

frontend/src/app/onboarding/page.tsx:
  "My Onboarding" — progress overview
  
  Top: welcome message with user's first name
  
  Progress cards (horizontal row):
    Textbook: ProgressRing showing chapter completion %
    Quizzes: ProgressRing showing quiz completion %
    Checklist: "Used {n} times" stat card
  
  Below: card grid:
    Card 1: "Textbook" → /onboarding/textbook
      Progress indicator: "Chapter X of Y"
      Gold "Continue Reading" button
    
    Card 2: "Quizzes" → /onboarding/quiz (index)
      Progress: "X of Y complete"
      Show "Final Assessment" badge if all chapter quizzes done
    
    Card 3: "Contract Checklist" → /onboarding/checklist
      "Review any contract against your org's standards"
    
    Card 4: "Ask the Playbook" → /onboarding/chat
      "Your org's contract knowledge, on demand"
  
  If not all content is ready: show "Content being prepared..." with spinner

--- SECTION 6: Commit ---

git add -A && git commit -m "feat: onboarding UI — textbook reader, interactive quizzes, checklist, RAG chat"
```

---

## Workflow 8 — Integration, Polish & Demo Prep

**Branch**: `workflow-8/integration-polish`
**Owns**: everything — final integration pass

---

**Claude Code Prompt:**

```
LexOnboard is feature-complete across Workflows 1-7. Now do a full integration and polish pass.

--- SECTION 1: End-to-End Integration Test ---

Write backend/tests/test_pipeline_integration.py:
  Use pytest + httpx AsyncClient
  Test: upload a small test PDF → verify Document created → poll until status=complete →
        verify ProcessedClause records exist → verify OrgPlaybook generated →
        verify TextbookContent generated
  Use a real small PDF: create backend/tests/fixtures/sample_contract.txt with 3 short contract clauses
  Convert to PDF in the test using fpdf2

Write backend/tests/test_api_auth.py:
  Test: unauthenticated request to /api/documents/ returns 401
  Test: authenticated request to another org's data returns 403 (or empty, not their data)

--- SECTION 2: Error States ---

Frontend: add error boundaries for each major section:
  If textbook fails to load: "Content still being generated. Check back in a few minutes." + retry button
  If chat fails: "Unable to connect. Make sure your documents have been processed." 
  If playbook is empty: helpful empty state with CTA to upload documents

Backend: ensure all Celery tasks update document status to "error" with a human-readable message on failure.
Add endpoint GET /api/documents/{id}/retry to re-enqueue a failed document.

--- SECTION 3: Performance ---

Backend:
  Add response caching for GET /api/playbook/current (Redis cache, 5-min TTL, invalidated on new playbook version)
  Add response caching for GET /api/onboarding/textbook and /checklist (same TTL)
  Use FastAPI BackgroundTasks for OnboardingProgress updates (fire-and-forget, don't block response)

Frontend:
  Add loading skeletons for all data-fetching components (not spinners — skeleton placeholder shapes)
  Use Next.js Image component for any images
  Prefetch /api/onboarding/textbook when user logs in as new_hire role

--- SECTION 4: Demo Mode ---

Add DEMO_MODE=true env flag.
When demo mode is on:
  - Pre-seed the DB with a fake org "Ironbridge Engineering Ltd." with:
    - 2 pre-processed documents (generate static JSON fixtures for ProcessedClause records)
    - A pre-built OrgPlaybook with 6 sections (stored as JSON fixture)
    - Pre-built TextbookContent, 2 QuizSets, ContractChecklist
  - Skip actual Celery pipeline (return mock job_id that immediately shows complete)
  - Chat still works against real Qdrant (seed Qdrant with fixture clause embeddings on startup)

Create backend/scripts/seed_demo.py that:
  1. Creates demo org + admin user + new_hire user
  2. Loads fixture JSON into DB
  3. Embeds fixture clauses into Qdrant

Add NPM script: "demo:seed" that runs seed_demo.py before starting dev server.

--- SECTION 5: README ---

Write a comprehensive README.md at root:
  - One-line description
  - Screenshot placeholder section
  - Prerequisites (Python 3.11, Node 18+, Docker)
  - Quick start: clone → copy .env.example → docker compose up → seed demo → open localhost:3000
  - Architecture diagram (ASCII art of the pipeline flow)
  - Environment variables table
  - API docs link (FastAPI auto-docs at /docs)

--- SECTION 6: Final Commit ---

git add -A && git commit -m "feat: integration polish, error states, demo mode, performance caching, README"
git push origin main
```

---

## Environment Variables Reference

```bash
# .env (backend)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/lexonboard
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333

ANTHROPIC_API_KEY=sk-ant-...

# Supabase — storage only (auth deferred to later phase)
# Uncomment when implementing auth:
# SUPABASE_URL=https://xxxx.supabase.co
# SUPABASE_SERVICE_KEY=eyJ...
# SUPABASE_STORAGE_BUCKET=documents
# Until then, files stored locally at /tmp/lexonboard/

ENVIRONMENT=development
DEMO_MODE=false

# .env.local (frontend)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Dev identity — swap these to simulate different roles/orgs
NEXT_PUBLIC_DEV_ORG_ID=dev-org-001
NEXT_PUBLIC_DEV_USER_ID=dev-user-001
NEXT_PUBLIC_DEV_USER_ROLE=admin    # "admin" | "new_hire"
```

---

## Build Order Summary

| Workflow | What Gets Built | Output |
|----------|----------------|--------|
| 1 | Backend foundation: models, schemas, Celery, no-auth dev deps | Buildable FastAPI with all DB tables |
| 2 | Ingestion + NLP: parser (text + OCR), chunker, NER, classifier, Celery task | Documents can be uploaded and processed end-to-end |
| 3 | Distillation + generation: Claude API synthesis, manual regen trigger, textbook, quizzes (100% pass), checklist, export | Full pipeline working end-to-end |
| 4 | RAG chat: retriever, chat service | New hires can query the playbook |
| 5 | Frontend foundation: no-auth dev context, layout, sidebar, role switcher | Shell navigates correctly for both roles |
| 6 | Dashboard + upload + pipeline status + playbook viewer | Admin can upload, track pipeline, view + export playbook |
| 7 | Onboarding UI: textbook, quizzes (100% mastery gate), checklist, RAG chat | Full new hire onboarding flow |
| 8 | Integration, polish, demo mode, README | Demo-ready |
| 6 | Dashboard + upload + playbook viewer | Admin can upload and view playbook |
| 7 | Onboarding UI: textbook, quizzes, checklist, chat | New hire onboarding complete |
| 8 | Integration, polish, demo mode | Demo-ready, production-ready |
