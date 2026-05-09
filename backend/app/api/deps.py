from fastapi import HTTPException, Request


def get_org_id(request: Request) -> str:
    # TODO: replace with real auth when auth is implemented
    org_id = request.headers.get("X-Org-ID") or request.query_params.get("org_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="X-Org-ID header is required")
    return org_id


def get_user_context(request: Request) -> dict:
    # TODO: replace with real auth when auth is implemented
    org_id = get_org_id(request)
    user_id = request.headers.get("X-User-ID", "dev-user-001")
    role = request.headers.get("X-User-Role", "admin")
    return {"user_id": user_id, "org_id": org_id, "role": role}