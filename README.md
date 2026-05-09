# LexOnboard

AI-powered legal contract onboarding — turns your org's contract history into a living knowledge base that new hires can actually learn from.

---

## Screenshots

_Screenshots coming soon. Run the demo to see the live UI._

---

## Prerequisites

- Python 3.11+
- Node 18+
- Docker + Docker Compose

---

## Quick Start

```bash
# 1. Clone
git clone git@github.com:VMotta1/LexOnboard.git
cd LexOnboard

# 2. Start infrastructure
docker compose up -d

# 3. Backend setup
cd backend
cp .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 4. Run DB migrations
python scripts/init_db.py

# 5. (Optional) Seed demo data — Ironbridge Engineering Ltd.
python scripts/seed_demo.py

# 6. Start backend
uvicorn app.main:app --reload --port 8000

# 7. Start Celery worker (new terminal)
cd backend && source venv/bin/activate
celery -A app.celery_app worker --loglevel=info

# 8. Frontend setup
cd frontend
cp .env.local.example .env.local
# If using demo: update NEXT_PUBLIC_DEV_ORG_ID per seed_demo.py output
npm install
npm run dev

# Open http://localhost:3000
```

---

## Architecture

```
                    ┌─────────────────────────────────────┐
                    │          Next.js 14 Frontend         │
                    │  Admin UI           New Hire UI      │
                    │  ─────────────      ─────────────    │
                    │  Upload docs        Textbook reader  │
                    │  Pipeline status    Interactive quiz │
                    │  Playbook viewer    Contract checklist│
                    │  Export (Word/PDF)  RAG chat         │
                    └─────────────┬───────────────────────┘
                                  │ HTTP (X-Org-ID header)
                    ┌─────────────▼───────────────────────┐
                    │         FastAPI Backend              │
                    │  /api/documents   /api/playbook      │
                    │  /api/pipeline    /api/onboarding    │
                    │  /api/chat                           │
                    └──────┬──────────────────┬───────────┘
                           │                  │
         ┌─────────────────▼──┐    ┌──────────▼────────────┐
         │    Celery Worker   │    │   Redis               │
         │                    │    │   Broker + Cache      │
         │  Pipeline A:       │    │   (5-min TTL)         │
         │  PDF/DOCX upload   │    └───────────────────────┘
         │  → Unstructured.io │
         │  → LegalBERT NER   │         ┌─────────────────┐
         │  → CUAD-RoBERTa    │         │   PostgreSQL    │
         │  → bge embeddings  │◄───────►│   12 tables     │
         │  → Qdrant upsert   │         │   org-scoped    │
         │                    │         └─────────────────┘
         │  Pipeline B:       │
         │  → Claude synthesis│         ┌─────────────────┐
         │  → OrgPlaybook     │         │   Qdrant        │
         │  → Textbook        │◄───────►│   384-dim COSINE│
         │  → Quizzes         │         │   org-filtered  │
         │  → Checklist       │         └─────────────────┘
         └────────────────────┘

  RAG Chat: question → bge embed → Qdrant search → top-5 clauses → Claude answer
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | ✓ | — | PostgreSQL connection string |
| `REDIS_URL` | ✓ | — | Redis connection string (broker + cache) |
| `QDRANT_URL` | ✓ | — | Qdrant vector DB URL |
| `ANTHROPIC_API_KEY` | ✓ | — | Claude API key (`claude-sonnet-4-20250514`) |
| `QDRANT_API_KEY` | — | `null` | Qdrant cloud API key (omit for local) |
| `SUPABASE_URL` | — | `null` | Supabase project URL (auth deferred) |
| `SUPABASE_SERVICE_KEY` | — | `null` | Supabase service role key (auth deferred) |
| `ENVIRONMENT` | — | `development` | `development` or `production` |
| `DEMO_MODE` | — | `false` | Skip Celery pipeline, use seeded fixtures |

### Frontend (`frontend/.env.local`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | — | `http://localhost:8000` | Backend API URL |
| `NEXT_PUBLIC_DEV_ORG_ID` | — | `dev-org-001` | Org ID sent as X-Org-ID header |
| `NEXT_PUBLIC_DEV_USER_ID` | — | `dev-user-001` | User ID sent as X-User-ID header |
| `NEXT_PUBLIC_DEV_USER_ROLE` | — | `admin` | Role: `admin`, `lawyer`, or `new_hire` |

---

## API Docs

FastAPI auto-generates interactive docs:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Running Tests

```bash
cd backend && source venv/bin/activate

# Auth isolation tests (no live infrastructure needed)
pytest tests/test_api_auth.py -v

# Full pipeline integration test (requires DB, Redis, Celery, Qdrant, Anthropic key)
pytest tests/test_pipeline_integration.py -m integration -v
```

---

## Demo Mode

Seeded with **Ironbridge Engineering Ltd.** — 6-section playbook, full textbook, quizzes, and contract checklist. Celery pipeline bypassed.

```bash
# Enable
echo "DEMO_MODE=true" >> backend/.env
python backend/scripts/seed_demo.py

# Then in frontend/.env.local:
# NEXT_PUBLIC_DEV_ORG_ID=00000000-0000-0000-0000-000000000001
# NEXT_PUBLIC_DEV_USER_ID=00000000-0000-0000-0000-000000000010  (admin)
# NEXT_PUBLIC_DEV_USER_ID=00000000-0000-0000-0000-000000000011  (new_hire)
```

---

## Auth

Intentionally deferred. Current system uses `X-Org-ID`, `X-User-ID`, `X-User-Role` headers for dev identity. Supabase Auth is a drop-in replacement in `backend/app/api/deps.py`.
