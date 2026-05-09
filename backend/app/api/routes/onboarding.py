from fastapi import APIRouter

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/textbook")
async def get_textbook():
    # TODO: replace get_org_id with real auth when auth is implemented
    return {"message": "not implemented"}


@router.get("/quizzes")
async def get_quizzes():
    # TODO: replace get_org_id with real auth when auth is implemented
    return {"message": "not implemented"}


@router.get("/checklist")
async def get_checklist():
    # TODO: replace get_org_id with real auth when auth is implemented
    return {"message": "not implemented"}


@router.get("/progress")
async def get_progress():
    # TODO: replace get_org_id with real auth when auth is implemented
    return {"message": "not implemented"}


@router.patch("/progress")
async def update_progress():
    # TODO: replace get_org_id with real auth when auth is implemented
    return {"message": "not implemented"}