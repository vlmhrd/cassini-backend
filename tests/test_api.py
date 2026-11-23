import hashlib

import pytest
from fastapi.testclient import TestClient

from cassini_backend.main import app

from .scenarios import honest_kyiv, lima_spoof

PHOTO = b"\xff\xd8 pretend jpeg bytes"
PHOTO_HASH = hashlib.sha256(PHOTO).hexdigest()


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.sqlite3"))
    monkeypatch.setenv("SIGNING_KEY_PATH", str(tmp_path / "signing.key"))
    with TestClient(app) as c:
        yield c


def issue(client, report):
    body = {"photo_sha256": PHOTO_HASH, "report": report.model_dump(), "device_integrity": "integrity_ok"}
    res = client.post("/certificates", json=body)
    assert res.status_code == 200, res.text
    return res.json()


def test_report_returns_status(client):
    res = client.post("/reports", json=lima_spoof().model_dump())
    assert res.json()["status"] == "red"


def test_honest_certificate_verifies(client):
    signed = issue(client, honest_kyiv())
    assert signed["certificate"]["status"] == "green"
    v = client.post("/verify", json=signed).json()
    assert v["signature_valid"] and v["known_certificate"]
    assert v["trust_level"] == "verified"


def test_photo_upload_matches(client):
    cid = issue(client, honest_kyiv())["certificate"]["id"]
    ok = client.post(f"/verify/{cid}/photo", files={"photo": ("p.jpg", PHOTO)}).json()
    bad = client.post(f"/verify/{cid}/photo", files={"photo": ("p.jpg", PHOTO + b"edited")}).json()
    assert ok["photo_matches"] and ok["trust_level"] == "verified"
    assert bad["photo_matches"] is False and bad["trust_level"] == "invalid"


def test_spoofed_certificate_has_recovered_location(client):
    cert = issue(client, lima_spoof())["certificate"]
    assert cert["status"] == "red"
    assert 50 < cert["lat"] < 51  # Kyiv, not Lima
    assert "galileo_vs_gps" in cert["flags"]


def test_tampered_certificate_is_invalid(client):
    signed = issue(client, lima_spoof())
    signed["certificate"]["status"] = "green"
    v = client.post("/verify", json=signed).json()
    assert not v["signature_valid"] and v["trust_level"] == "invalid"
