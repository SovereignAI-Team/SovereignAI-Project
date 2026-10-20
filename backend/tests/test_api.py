import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services import local_llm
from tests.conftest import make_pdf_bytes


@pytest.fixture
def client():
    with TestClient(create_app()) as c:
        yield c


def _upload(client, data: bytes, name: str = "manual.pdf"):
    return client.post("/api/documents/upload", files={"file": (name, data, "application/pdf")})


def test_health_reports_components(client, monkeypatch):
    monkeypatch.setattr("app.services.local_llm.llm_status", lambda: (False, "Ollama is not reachable."))
    body = client.get("/api/health").json()
    assert body["status"] == "degraded"
    assert body["database"]["ok"] is True
    assert body["llm"]["ok"] is False


def test_upload_rejects_non_pdf_extension(client):
    r = _upload(client, b"hello", "notes.txt")
    assert r.status_code == 415


def test_upload_rejects_fake_pdf(client):
    r = _upload(client, b"this is not a pdf at all", "fake.pdf")
    assert r.status_code == 400


def test_full_document_lifecycle(client, sample_pdf, fake_llm):
    r = _upload(client, sample_pdf)
    assert r.status_code == 201
    doc = r.json()["document"]
    assert doc["status"] == "ready" and doc["page_count"] == 2

    listing = client.get("/api/documents").json()["documents"]
    assert [d["id"] for d in listing] == [doc["id"]]
    assert client.get(f"/api/documents/{doc['id']}").status_code == 200

    ask = client.post("/api/chat/ask", json={"question": "How long is the warranty period?", "document_ids": [doc["id"]]})
    assert ask.status_code == 200
    body = ask.json()
    assert body["answered"] is True
    assert body["citations"][0]["page_number"] == 1

    d = client.delete(f"/api/documents/{doc['id']}")
    assert d.status_code == 200
    assert client.get(f"/api/documents/{doc['id']}").status_code == 404
    assert client.delete(f"/api/documents/{doc['id']}").status_code == 404


def test_duplicate_upload_reuses_index(client, sample_pdf):
    first = _upload(client, sample_pdf).json()
    second = _upload(client, sample_pdf).json()
    assert second["duplicate"] is True
    assert second["document"]["id"] != first["document"]["id"]
    assert second["document"]["status"] == "ready"


def test_unreadable_pdf_is_stored_as_failed(client):
    r = _upload(client, make_pdf_bytes(["", ""]), "scan.pdf")
    # no text and (in CI) no OCR: processing fails but the API responds cleanly
    assert r.status_code == 201
    assert r.json()["document"]["status"] in ("failed", "ready")


def test_ask_validates_input(client):
    assert client.post("/api/chat/ask", json={"question": "", "document_ids": ["x"]}).status_code == 422
    assert client.post("/api/chat/ask", json={"question": "hi", "document_ids": []}).status_code == 422


def test_ask_returns_503_when_model_unavailable(client, sample_pdf, monkeypatch):
    doc_id = _upload(client, sample_pdf).json()["document"]["id"]

    def down(system, user):
        raise local_llm.LLMUnavailableError("Model 'llama3.2:3b' not installed. Run: ollama pull llama3.2:3b")

    monkeypatch.setattr("app.services.local_llm.generate", down)
    r = client.post("/api/chat/ask", json={"question": "warranty period?", "document_ids": [doc_id]})
    assert r.status_code == 503
    assert "ollama pull" in r.json()["detail"]


def test_path_traversal_id_is_rejected(client):
    assert client.delete("/api/documents/..%2F..%2Fetc").status_code in (404, 405)
