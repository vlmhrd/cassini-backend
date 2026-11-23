"""Demo scenarios as synthetic reports. Attacks are simulated in software only —
never transmit fake GNSS signals."""

from cassini_backend.models import Report

T = 1_795_000_000_000  # an arbitrary Unix-ms timestamp
KYIV = {"lat": 50.4501, "lon": 30.5234}
LIMA = {"lat": -12.0464, "lon": -77.0428}


def sats(cn0s: list[float], constellation: str = "GALILEO") -> list[dict]:
    return [{"svid": i + 1, "constellation": constellation, "cn0_dbhz": c} for i, c in enumerate(cn0s)]


def honest_kyiv(session_id: str = "honest") -> Report:
    return Report(
        session_id=session_id,
        fix={**KYIV, "time_ms": T},
        galileo_fix={"lat": 50.45012, "lon": 30.52345, "time_ms": T},
        gps_fix={"lat": 50.45008, "lon": 30.52338, "time_ms": T},
        satellites=sats([31, 38, 42, 27, 44, 36, 29, 40]),
        osnma_ok=True,
        osnma_sats=7,
        cell_position={"lat": 50.452, "lon": 30.520},
        wifi_positions=[{"lat": 50.4502, "lon": 30.5236}, {"lat": 50.4499, "lon": 30.5231}],
        network_time_ms=T + 300,
    )


def lima_spoof(session_id: str = "lima") -> Report:
    """GPS L1 spoofed to Lima; authenticated Galileo, cell and Wi-Fi still say Kyiv."""
    return Report(
        session_id=session_id,
        fix={**LIMA, "time_ms": T},
        galileo_fix={"lat": 50.45015, "lon": 30.52350, "time_ms": T},
        gps_fix={**LIMA, "time_ms": T},
        satellites=sats([45.1, 45.3, 44.9, 45.0, 45.2, 44.8]),  # spoofer: uniform, strong
        osnma_ok=True,
        osnma_sats=6,
        cell_position={"lat": 50.452, "lon": 30.520},
        wifi_positions=[{"lat": 50.4502, "lon": 30.5236}, {"lat": 50.4499, "lon": 30.5231}],
        network_time_ms=T + 300,
    )
