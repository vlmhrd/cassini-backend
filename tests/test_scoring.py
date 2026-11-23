from cassini_backend.geo import dist_m
from cassini_backend.models import LatLon, Report
from cassini_backend.scoring import trust_score

from .scenarios import KYIV, T, honest_kyiv, lima_spoof, sats


def test_honest_photo_is_green():
    r = trust_score(honest_kyiv())
    assert r.status == "green"
    assert r.flags == []
    assert r.source == "gnss"


def test_lima_spoof_is_red_and_recovers_kyiv():
    r = trust_score(lima_spoof())
    names = {f.name for f in r.flags}
    assert r.status == "red"
    assert {"galileo_vs_gps", "gnss_vs_cell", "uniform_cn0"} <= names
    assert dist_m(r.best_estimate, LatLon(**KYIV)) < 100


def test_impossible_jump():
    prev = honest_kyiv().fix
    jumped = honest_kyiv().model_copy(update={"fix": prev.model_copy(update={"lat": 50.55, "time_ms": T + 5000})})
    assert "impossible_jump" in {f.name for f in trust_score(jumped, prev_fix=prev).flags}


def test_jamming_falls_back_to_wifi():
    r = trust_score(Report(**{**honest_kyiv().model_dump(), "satellites": sats([15, 14])}))
    assert "jamming" in {f.name for f in r.flags}
    assert r.status == "amber" and r.source == "wifi"


def test_no_evidence_gives_no_location():
    r = trust_score(Report(session_id="x", osnma_ok=False, satellites=[]))
    assert r.status == "red" and r.best_estimate is None
