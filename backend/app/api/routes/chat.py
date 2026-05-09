from fastapi import APIRouter

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/query")
async def query_chat():
    # TODO: replace get_org_id with real auth when auth is implemented
    return {"message": "not implemented"}


@router.get("/history")
async def get_chat_history():
    # TODO: replace get_org_id with real auth when auth is implemented
    return {"message": "not implemented"}