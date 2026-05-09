from fastapi import APIRouter

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/status/{job_id}")
async def get_pipeline_status(job_id: str):
    # TODO: replace get_org_id with real auth when auth is implemented
    return {"message": "not implemented"}