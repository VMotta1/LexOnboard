from fastapi import APIRouter

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document():
    # TODO: replace get_org_id with real auth when auth is implemented
    return {"message": "not implemented"}


@router.get("/")
async def list_documents():
    # TODO: replace get_org_id with real auth when auth is implemented
    return {"message": "not implemented"}


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    # TODO: replace get_org_id with real auth when auth is implemented
    return {"message": "not implemented"}


@router.get("/{doc_id}/retry")
async def retry_document(doc_id: str):
    # TODO: replace get_org_id with real auth when auth is implemented
    return {"message": "not implemented"}