"""
Integration test: upload → pipeline → playbook.
Requires live DB, Redis, Celery worker, Qdrant, and Anthropic API key.
Mark: pytest -m integration
"""
import asyncio
import io
import os
import pathlib
import time
import uuid

import pytest
import pytest_asyncio
from fpdf import FPDF
from httpx import AsyncClient, ASGITransport

from app.main import app

FIXTURE_DIR = pathlib.Path(__file__).parent / "fixtures"
ORG_ID = str(uuid.uuid4())
USER_ID = str(uuid.uuid4())
HEADERS = {"X-Org-ID": ORG_ID, "X-User-ID": USER_ID, "X-User-Role": "admin"}
POLL_INTERVAL = 3
POLL_TIMEOUT = 300  # 5 min — NLP + Claude can be slow


def _build_pdf() -> bytes:
    """Convert sample_contract.txt → in-memory PDF using fpdf2."""
    text = (FIXTURE_DIR / "sample_contract.txt").read_text()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    pdf.set_auto_page_break(auto=True, margin=15)
    for line in text.splitlines():
        pdf.multi_cell(0, 6, line or " ")
    return pdf.output()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_pipeline():
    pdf_bytes = _build_pdf()
    file_obj = io.BytesIO(pdf_bytes)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Upload document
        response = await client.post(
            "/api/documents/upload",
            headers={k: v for k, v in HEADERS.items() if k != "Content-Type"},
            files={"file": ("sample_contract.pdf", file_obj, "application/pdf")},
            data={"doc_type": "Master Agreement"},
        )
        assert response.status_code == 200, response.text
        upload_data = response.json()
        doc_id = upload_data["id"]
        job_id = upload_data.get("job_id")
        assert doc_id
        assert job_id

        # 2. Poll pipeline until complete
        deadline = time.time() + POLL_TIMEOUT
        final_status = None
        while time.time() < deadline:
            status_resp = await client.get(
                f"/api/pipeline/status/{job_id}",
                headers=HEADERS,
            )
            assert status_resp.status_code == 200
            data = status_resp.json()
            if data["status"] in ("complete", "error"):
                final_status = data["status"]
                break
            await asyncio.sleep(POLL_INTERVAL)

        assert final_status == "complete", f"Pipeline did not complete: {final_status}"

        # 3. Verify ProcessedClause records exist
        docs_resp = await client.get("/api/documents/", headers=HEADERS)
        assert docs_resp.status_code == 200
        docs = docs_resp.json()
        matching = [d for d in docs if d["id"] == doc_id]
        assert len(matching) == 1
        assert matching[0]["status"] == "complete"

        # 4. Trigger playbook regeneration
        regen_resp = await client.post("/api/playbook/regenerate", headers=HEADERS)
        assert regen_resp.status_code in (200, 202)

        # Poll for playbook
        deadline = time.time() + POLL_TIMEOUT
        playbook = None
        while time.time() < deadline:
            pb_resp = await client.get("/api/playbook/current", headers=HEADERS)
            if pb_resp.status_code == 200:
                playbook = pb_resp.json()
                if playbook.get("onboarding_ready"):
                    break
            await asyncio.sleep(POLL_INTERVAL)

        assert playbook is not None, "Playbook never became available"
        assert playbook["onboarding_ready"] is True, "Playbook not marked onboarding_ready"

        # 5. Verify TextbookContent exists
        tb_resp = await client.get("/api/onboarding/textbook", headers=HEADERS)
        assert tb_resp.status_code == 200
        textbook = tb_resp.json()
        assert len(textbook["chapters"]) > 0
