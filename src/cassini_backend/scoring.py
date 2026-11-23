"""Rule-based location trust scoring (build plan, section 3).

Each check that fires adds a weighted flag with a human-readable "why".
Risk < 0.3 is green, < 0.6 amber, otherwise red. Thresholds are first guesses
and need calibrating per phone model on recorded logs.
"""

from statistics import mean, pstdev

from .eo import EOContext, NullEO
from .geo import dist_m, filter_outliers, median_point
from .models import Fix, Flag, Report, TrustResult

GAL_GPS_MAX_DIFF_M = 100
MAX_GROUND_SPEED_MS = 70
MAX_CELL_DIST_M = 5_000
UNIFORM_CN0_STDEV_DB = 2
WEAK_CN0_DBHZ = 20
MAX_TIME_DIFF_MS = 10_000
WIFI_OUTLIER_M = 1_000

WIFI_RADIUS_M = 150
CELL_RADIUS_M = 2_000
GNSS_RADIUS_M = 20


def trust_score(report: Report, prev_fix: Fix | None = None, eo: EOContext | None = None) -> TrustResult:
    eo = eo or NullEO()
    fix = report.fix
    flags: list[Flag] = []

    def flag(name: str, weight: float, why: str) -> None:
        flags.append(Flag(name=name, weight=weight, why=why))

    if report.osnma_ok is False:
        flag("osnma_fail", 0.5, "Galileo navigation signatures did not authenticate")

    gal_gps_diff = None
    if report.galileo_fix and report.gps_fix:
        gal_gps_diff = dist_m(report.galileo_fix, report.gps_fix)
        if gal_gps_diff > GAL_GPS_MAX_DIFF_M:
            flag("galileo_vs_gps", 0.4, f"Galileo-only and GPS-only fixes are {gal_gps_diff:.0f} m apart")

    if fix and prev_fix and fix.time_ms > prev_fix.time_ms:
        speed = dist_m(fix, prev_fix) / ((fix.time_ms - prev_fix.time_ms) / 1000)
        if speed > MAX_GROUND_SPEED_MS:
            flag("impossible_jump", 0.4, f"Position jumped at {speed:.0f} m/s since the previous fix")

    if fix and report.cell_position:
        d = dist_m(fix, report.cell_position)
        if d > MAX_CELL_DIST_M:
            flag("gnss_vs_cell", 0.4, f"GNSS fix is {d / 1000:.0f} km from the serving cell tower")

    cn0 = [s.cn0_dbhz for s in report.satellites]
    if len(cn0) >= 6 and pstdev(cn0) < UNIFORM_CN0_STDEV_DB and mean(cn0) > 35:
        flag("uniform_cn0", 0.3, f"Signal strength is suspiciously uniform ({pstdev(cn0):.1f} dB spread)")

    weak = len(cn0) < 4 or (bool(cn0) and mean(cn0) < WEAK_CN0_DBHZ)
    if weak and not (fix and eo.dense_urban(fix)):
        flag("jamming", 0.5, f"Weak GNSS: {len(cn0)} satellites tracked")

    if fix and report.network_time_ms is not None:
        dt = abs(fix.time_ms - report.network_time_ms)
        if dt > MAX_TIME_DIFF_MS:
            flag("time_mismatch", 0.3, f"GNSS time differs from network time by {dt / 1000:.0f} s")

    wifi = filter_outliers(report.wifi_positions, WIFI_OUTLIER_M)
    if fix and eo.damaged(fix):
        wifi = []  # routers in destroyed buildings are likely stale in the databases

    risk = round(min(1.0, sum(f.weight for f in flags)), 3)
    status = "green" if risk < 0.3 else "amber" if risk < 0.6 else "red"

    if status == "green" and fix:
        best, radius, source = fix, GNSS_RADIUS_M, "gnss"
    elif report.osnma_ok and report.galileo_fix and "galileo_vs_gps" in {f.name for f in flags}:
        # GPS disagrees with *authenticated* Galileo: trust Galileo.
        best, radius, source = report.galileo_fix, GNSS_RADIUS_M, "gnss"
    elif wifi:
        best, radius, source = median_point(wifi), WIFI_RADIUS_M, "wifi"
    elif report.cell_position:
        best, radius, source = report.cell_position, CELL_RADIUS_M, "cell"
    else:
        best, radius, source = None, None, "none"

    return TrustResult(
        status=status,
        risk=risk,
        best_estimate=best and {"lat": best.lat, "lon": best.lon},
        radius_m=radius,
        source=source,
        flags=flags,
    )


def galileo_gps_diff(report: Report) -> float | None:
    if report.galileo_fix and report.gps_fix:
        return round(dist_m(report.galileo_fix, report.gps_fix), 1)
    return None
