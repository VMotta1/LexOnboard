#!/usr/bin/env bash
# Start the LexOnboard FastAPI backend with the env vars and import order
# required to avoid `OMP: Error #179` on macOS arm64.
#
# Run from the backend directory after `source venv/bin/activate`:
#   ./scripts/run_api.sh

set -euo pipefail

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

# Use `python -c` so PyTorch is imported before uvicorn's asyncio/threadpools.
# Importing torch first while the interpreter is still in early init prevents
# libomp's later `shm_open` calls from failing with `SHM2 No such file or directory`.
exec python -c "
import torch
torch.set_num_threads(1)
import uvicorn
uvicorn.run('app.main:app', host='127.0.0.1', port=8000, log_level='info')
"
