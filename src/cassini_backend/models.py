"""Request/response schemas shared by the API, scoring engine and certificates."""

from typing import Literal

from pydantic import BaseModel, Field

Status = Literal["green", "amber", "red"]


class LatLon(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class Fix(LatLon):
    """A position fix with the GNSS time it was computed for (Unix ms)."""

    alt_m: float | None = None
    time_ms: int


class Satellite(BaseModel):
    svid: int
    constellation: Literal["GPS", "GALILEO", "GLONASS", "BEIDOU", "QZSS", "SBAS", "OTHER"]
    cn0_dbhz: float


class Report(BaseModel):
    """One upload from the phone collector (every ~5 s, or at photo capture).

    Cell and Wi-Fi positions are expected already resolved for now; lookup via
    OpenCellID / WiGLE comes later.
    """

    session_id: str = Field(description="Random per-install id; never a user identity")
    fix: Fix | None = Field(None, description="The phone's fused GNSS fix")
    galileo_fix: Fix | None = None
    gps_fix: Fix | None = None
    satellites: list[Satellite] = []
    osnma_ok: bool | None = Field(None, description="None = not checked / no nav pages")
    osnma_sats: int = 0
    cell_position: LatLon | None = None
    wifi_positions: list[LatLon] = []
    network_time_ms: int | None = None


class Flag(BaseModel):
    name: str
    weight: float
    why: str


class TrustResult(BaseModel):
    status: Status
    risk: float
    best_estimate: LatLon | None
    radius_m: float | None
    source: Literal["gnss", "wifi", "cell", "none"]
    flags: list[Flag]


class CertificateRequest(BaseModel):
    photo_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    report: Report
    device_integrity: Literal["integrity_ok", "integrity_failed", "unknown"] = "unknown"


class Certificate(BaseModel):
    id: str
    photo_sha256: str
    time_ms: int
    lat: float | None
    lon: float | None
    radius_m: float | None
    location_source: str
    status: Status
    osnma_sats: int
    gal_gps_diff_m: float | None
    flags: list[str]
    device: str
    eo_damage: Literal["pending", "change_detected", "no_change", "unavailable"] = "pending"
    issued_at_ms: int


class SignedCertificate(BaseModel):
    certificate: Certificate
    signature: str = Field(description="Base64 Ed25519 signature over canonical JSON")
    public_key: str = Field(description="Base64 Ed25519 verify key")


class VerifyResult(BaseModel):
    signature_valid: bool
    photo_matches: bool | None
    known_certificate: bool
    trust_level: Literal["verified", "partially_verified", "location_untrusted", "invalid"]
    certificate: Certificate | None
