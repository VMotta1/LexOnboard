#!/usr/bin/env bash
# Start the LexOnboard Celery worker with the env vars required to avoid
# `OMP: Error #179: Function Can't open SHM2 failed` on macOS arm64.
#
# Run from the backend directory after `source venv/bin/activate`:
#   ./scripts/run_worker.sh

set -euo pipefail

# macOS-safe OpenMP/BLAS configuration. KMP_LIBRARY=serial is the critical one:
# it disables libomp's thread-pool init that calls shm_open(), which fails on
# macOS arm64 with `OMP: Error #179`.
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

exec celery -A app.celery_app worker \
    --loglevel=info \
    --pool=solo \
    --without-heartbeat \
    --without-gossip \
    --without-mingle
