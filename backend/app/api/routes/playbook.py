from fastapi import APIRouter

router = APIRouter(prefix="/playbook", tags=["playbook"])


@router.get("/current")
async def get_current_playbook():
    # TODO: replace get_org_id with real auth when auth is implemented
    return {"message": "not implemented"}


@router.get("/versions")
async def list_playbook_versions():
    # TODO: replace get_org_id with real auth when auth is implemented
    return {"message": "not implemented"}


@router.post("/regenerate")
async def regenerate_playbook():
    # TODO: replace get_org_id with real auth when auth is implemented
    return {"message": "not implemented"}


@router.get("/regenerate/status")
async def get_regenerate_status():
    # TODO: replace get_org_id with real auth when auth is implemented
    return {"message": "not implemented"}


@router.post("/export")
async def export_playbook():
    # TODO: replace get_org_id with real auth when auth is implemented
    return {"message": "not implemented"}


@router.patch("/sections/{clause_type}")
async def update_playbook_section(clause_type: str):
    # TODO: replace get_org_id with real auth when auth is implemented
    return {"message": "not implemented"}