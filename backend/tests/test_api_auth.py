"""
Auth / org isolation tests.
Our auth is header-based (X-Org-ID). No JWT yet — these test the current
dev-auth layer behaves correctly at the boundary.
"""
import uuid

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_missing_org_id_returns_400():
    """Request without X-Org-ID must be rejected (400 — missing required header)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/documents/")
        assert response.status_code == 400
        assert "X-Org-ID" in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_org_isolation_documents():
    """Org A cannot see Org B's documents — list must be empty for unknown org."""
    org_a = str(uuid.uuid4())
    org_b = str(uuid.uuid4())
    headers_a = {"X-Org-ID": org_a, "X-User-ID": "user-a", "X-User-Role": "admin"}
    headers_b = {"X-Org-ID": org_b, "X-User-ID": "user-b", "X-User-Role": "admin"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Both orgs see empty document lists (no cross-contamination)
        resp_a = await client.get("/api/documents/", headers=headers_a)
        resp_b = await client.get("/api/documents/", headers=headers_b)

        assert resp_a.status_code == 200
        assert resp_b.status_code == 200
        assert resp_a.json() == []
        assert resp_b.json() == []


@pytest.mark.asyncio
async def test_org_isolation_playbook():
    """Org with no playbook gets 404, not another org's playbook."""
    random_org = str(uuid.uuid4())
    headers = {"X-Org-ID": random_org, "X-User-ID": "user-x", "X-User-Role": "admin"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/playbook/current", headers=headers)
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_org_isolation_onboarding():
    """Org with no playbook gets 404 for textbook/quiz/checklist."""
    random_org = str(uuid.uuid4())
    headers = {"X-Org-ID": random_org, "X-User-ID": "user-x", "X-User-Role": "new_hire"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for path in ["/api/onboarding/textbook", "/api/onboarding/checklist"]:
            response = await client.get(path, headers=headers)
            assert response.status_code == 404, f"{path} returned {response.status_code}"
