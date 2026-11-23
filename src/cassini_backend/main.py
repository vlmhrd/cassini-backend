import hashlib
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile

from . import certs
from .db import DB
from .models import (
    Certificate,
    CertificateRequest,
    Report,
    SignedCertificate,
    TrustResult,
    VerifyResult,
)
from .scoring import galileo_gps_diff, trust_score

state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    state["db"] = DB()
    state["key"] = certs.load_or_create_key()
    yield


app = FastAPI(title="cassini-backend", lifespan=lifespan)


def public_key() -> str:
    return certs.b64(bytes(state["key"].verify_key))


def score_and_store(report: Report) -> TrustResult:
    db: DB = state["db"]
    result = trust_score(report, prev_fix=db.last_fix(report.session_id))
    db.add_report(report.session_id, report.model_dump(), result.status, result.risk)
    if result.status == "green" and report.fix:
        db.set_last_fix(report.session_id, report.fix)
    return result


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/public-key")
def get_public_key() -> dict:
    return {"algorithm": "Ed25519", "public_key": public_key()}


@app.post("/reports")
def post_report(report: Report) -> TrustResult:
    """Periodic collector upload: returns the live trust status for the app indicator."""
    return score_and_store(report)


@app.post("/certificates")
def issue_certificate(req: CertificateRequest) -> SignedCertificate:
    """Called at photo capture with the photo hash and the evidence bundle."""
    r = req.report
    result = score_and_store(r)
    best = result.best_estimate
    now_ms = int(time.time() * 1000)
    cert = Certificate(
        id=uuid.uuid4().hex,
        photo_sha256=req.photo_sha256,
        # Trusted time: network time when available, never raw GNSS time under spoofing.
        time_ms=r.network_time_ms or (r.fix.time_ms if r.fix and result.status == "green" else now_ms),
        lat=best.lat if best else None,
        lon=best.lon if best else None,
        radius_m=result.radius_m,
        location_source=result.source,
        status=result.status,
        osnma_sats=r.osnma_sats,
        gal_gps_diff_m=galileo_gps_diff(r),
        flags=[f.name for f in result.flags],
        device=req.device_integrity,
        issued_at_ms=now_ms,
    )
    signed = SignedCertificate(certificate=cert, signature=certs.sign(cert, state["key"]), public_key=public_key())
    state["db"].add_certificate(signed)
    return signed


@app.get("/certificates/{cert_id}")
def get_certificate(cert_id: str) -> SignedCertificate:
    signed = state["db"].get_certificate(cert_id)
    if not signed:
        raise HTTPException(404, "certificate not found")
    return signed


def trust_level(cert: Certificate) -> str:
    if cert.status == "green" and cert.osnma_sats > 0:
        return "verified"
    if cert.lat is not None and cert.location_source != "none":
        return "partially_verified"
    return "location_untrusted"


@app.post("/verify")
async def verify(signed: SignedCertificate) -> VerifyResult:
    """Check a certificate's signature (e.g. pasted from a QR code / evidence package)."""
    return _verify(signed, photo_sha256=None)


@app.post("/verify/{cert_id}/photo")
async def verify_photo(cert_id: str, photo: UploadFile) -> VerifyResult:
    """Upload the original photo bytes; recompute the hash and check the stored certificate."""
    signed = state["db"].get_certificate(cert_id)
    if not signed:
        raise HTTPException(404, "certificate not found")
    return _verify(signed, photo_sha256=hashlib.sha256(await photo.read()).hexdigest())


def _verify(signed: SignedCertificate, photo_sha256: str | None) -> VerifyResult:
    # Only our own key counts; a certificate signed by any other key is invalid.
    valid = signed.public_key == public_key() and certs.verify(signed.certificate, signed.signature, public_key())
    stored = state["db"].get_certificate(signed.certificate.id)
    known = stored is not None and stored.signature == signed.signature
    matches = None if photo_sha256 is None else photo_sha256 == signed.certificate.photo_sha256
    ok = valid and known and matches is not False
    return VerifyResult(
        signature_valid=valid,
        photo_matches=matches,
        known_certificate=known,
        trust_level=trust_level(signed.certificate) if ok else "invalid",
        certificate=signed.certificate if valid else None,
    )
