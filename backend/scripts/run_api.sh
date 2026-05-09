#!/usr/bin/env bash
# Start the LexOnboard FastAPI backend.
# Handles macOS arm64 libomp/OMP:Error#179 by pre-importing torch before uvicorn.
# Idempotent: kills any existing process on port 8000 before starting.
#
# Usage (from repo root):   bash backend/scripts/run_api.sh
# Usage (from backend/):    bash scripts/run_api.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV="$BACKEND_DIR/venv"
LOG_FILE="/tmp/lexonboard-api.log"

# ── Kill any process already on port 8000 ────────────────────────────────────
PORT=8000
EXISTING=$(lsof -ti tcp:$PORT 2>/dev/null || true)
if [ -n "$EXISTING" ]; then
  echo "Killing existing process on port $PORT (PID $EXISTING)..."
  kill -9 $EXISTING 2>/dev/null || true
  sleep 1
fi

# ── Activate venv ─────────────────────────────────────────────────────────────
if [ ! -f "$VENV/bin/activate" ]; then
  echo "ERROR: venv not found at $VENV" >&2
  echo "Run: python3.11 -m venv $VENV && $VENV/bin/pip install -r $BACKEND_DIR/requirements.txt" >&2
  exit 1
fi
source "$VENV/bin/activate"

# ── macOS arm64 env vars ──────────────────────────────────────────────────────
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export KMP_DUPLICATE_LIB_OK=TRUE
export KMP_INIT_AT_FORK=FALSE
export KMP_AFFINITY=disabled
export KMP_LIBRARY=serial
export LEXONBOARD_INLINE_PROCESSING=true

cd "$BACKEND_DIR"

echo "Starting LexOnboard API on http://127.0.0.1:$PORT  (log: $LOG_FILE)"

# Pre-import torch before uvicorn to prevent macOS shm_open/libomp crash
exec python -c "
import torch
torch.set_num_threads(1)
import uvicorn
uvicorn.run('app.main:app', host='127.0.0.1', port=$PORT, log_level='info')
" 2>&1 | tee "$LOG_FILE"
