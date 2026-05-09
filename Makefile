SHELL := /bin/bash
ROOT := $(shell pwd)
BACKEND := $(ROOT)/backend
FRONTEND := $(ROOT)/frontend
API_LOG := /tmp/lexonboard-api.log
NEXT_LOG := /tmp/lexonboard-next.log

.PHONY: up down restart logs health install

## ── Bring everything up ──────────────────────────────────────────────────────
up:
	@echo "==> Starting infrastructure..."
	docker compose up -d
	@echo "==> Waiting for Postgres..."
	@until docker compose exec -T postgres pg_isready -U postgres -q 2>/dev/null; do sleep 1; done
	@echo "==> Starting API (background)..."
	@bash $(BACKEND)/scripts/run_api.sh &> $(API_LOG) &
	@echo "==> Waiting for API on :8000..."
	@for i in $$(seq 1 30); do \
		curl -sf http://127.0.0.1:8000/health > /dev/null 2>&1 && break || sleep 2; \
	done
	@echo "==> Starting Next.js (background)..."
	@cd $(FRONTEND) && npm run dev &> $(NEXT_LOG) &
	@echo ""
	@echo "Stack started:"
	@echo "  API   → http://localhost:8000"
	@echo "  Docs  → http://localhost:8000/docs"
	@echo "  App   → http://localhost:3000"
	@echo "  Logs  → make logs"

## ── Tear everything down ─────────────────────────────────────────────────────
down:
	@echo "==> Stopping API and Next.js..."
	@lsof -ti tcp:8000 | xargs kill -9 2>/dev/null || true
	@lsof -ti tcp:3000 | xargs kill -9 2>/dev/null || true
	@echo "==> Stopping Docker services..."
	docker compose down
	@echo "Done."

## ── Restart ──────────────────────────────────────────────────────────────────
restart: down up

## ── Tail logs ────────────────────────────────────────────────────────────────
logs:
	@echo "=== API log ($(API_LOG)) ===" && tail -50 $(API_LOG) 2>/dev/null || true
	@echo ""
	@echo "=== Next.js log ($(NEXT_LOG)) ===" && tail -20 $(NEXT_LOG) 2>/dev/null || true

## ── Health check ─────────────────────────────────────────────────────────────
health:
	@echo "==> Backend:"
	@curl -sf http://localhost:8000/health && echo " OK" || echo " DOWN"
	@echo "==> Frontend:"
	@curl -sf -o /dev/null -w "  HTTP %{http_code}\n" http://localhost:3000 || echo "  DOWN"
	@echo "==> Postgres:"
	@docker compose exec -T postgres pg_isready -U postgres 2>/dev/null && echo "  OK" || echo "  DOWN"
	@echo "==> Redis:"
	@docker compose exec -T redis redis-cli ping 2>/dev/null || echo "  DOWN"
	@echo "==> Qdrant:"
	@curl -sf http://localhost:6333/healthz && echo " OK" || echo " DOWN"

## ── First-time install ───────────────────────────────────────────────────────
install:
	@echo "==> Setting up Python venv..."
	python3.11 -m venv $(BACKEND)/venv
	$(BACKEND)/venv/bin/pip install --upgrade pip
	$(BACKEND)/venv/bin/pip install -r $(BACKEND)/requirements.txt
	@echo "==> Installing frontend deps..."
	cd $(FRONTEND) && npm install
	@echo "==> Done. Copy backend/.env.example → backend/.env and add secrets."
