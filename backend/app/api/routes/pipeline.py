import json
import logging

from fastapi import APIRouter, HTTPException

from app.schemas.document import PipelineStatusResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


def _redis():
    import redis

    from app.config import settings

    return redis.from_url(settings.REDIS_URL, decode_responses=True)


@router.get("/status/{job_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(job_id: str):
    # TODO: replace get_org_id with real auth when auth is implemented

    # Primary: pull from Redis
    try:
        r = _redis()
        raw = r.get(f"job:{job_id}")
        if raw:
            data = json.loads(raw)
            return PipelineStatusResponse(
                job_id=job_id,
                stage=data.get("stage", "unknown"),
                progress_pct=int(data.get("progress_pct", 0)),
                error=data.get("error"),
                document_id=data.get("document_id"),
            )
    except Exception as exc:
        logger.warning(f"Redis lookup failed for job {job_id}: {exc}")

    # Fallback: Celery AsyncResult
    try:
        from celery.result import AsyncResult

        from app.celery_app import celery_app

        result = AsyncResult(job_id, app=celery_app)
        state = result.state  # PENDING, STARTED, SUCCESS, FAILURE, RETRY

        stage_map = {
            "PENDING": "queued",
            "STARTED": "ingesting",
            "SUCCESS": "complete",
            "FAILURE": "error",
            "RETRY": "queued",
        }
        stage = stage_map.get(state, "unknown")
        error = str(result.result) if state == "FAILURE" else None

        return PipelineStatusResponse(
            job_id=job_id,
            stage=stage,
            progress_pct=100 if stage == "complete" else 0,
            error=error,
            document_id=None,
        )
    except Exception as exc:
        logger.error(f"Celery fallback also failed for job {job_id}: {exc}")
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found.",
        )