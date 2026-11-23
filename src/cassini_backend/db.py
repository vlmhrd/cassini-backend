"""SQLite storage. Hashes, certificates and evidence bundles only — never photos."""

import json
import os
import sqlite3
import time

from .models import Fix, SignedCertificate

SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY,
    session_id TEXT NOT NULL,
    received_at_ms INTEGER NOT NULL,
    payload TEXT NOT NULL,
    status TEXT NOT NULL,
    risk REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS reports_session ON reports(session_id, id);
CREATE TABLE IF NOT EXISTS last_trusted_fix (
    session_id TEXT PRIMARY KEY,
    fix TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS certificates (
    id TEXT PRIMARY KEY,
    photo_sha256 TEXT NOT NULL,
    signed TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS certificates_hash ON certificates(photo_sha256);
"""


class DB:
    def __init__(self, path: str | None = None):
        self.conn = sqlite3.connect(path or os.environ.get("DB_PATH", "data.sqlite3"), check_same_thread=False)
        self.conn.executescript(SCHEMA)

    def add_report(self, session_id: str, payload: dict, status: str, risk: float) -> None:
        self.conn.execute(
            "INSERT INTO reports(session_id, received_at_ms, payload, status, risk) VALUES (?,?,?,?,?)",
            (session_id, int(time.time() * 1000), json.dumps(payload), status, risk),
        )
        self.conn.commit()

    def last_fix(self, session_id: str) -> Fix | None:
        row = self.conn.execute("SELECT fix FROM last_trusted_fix WHERE session_id=?", (session_id,)).fetchone()
        return Fix.model_validate_json(row[0]) if row else None

    def set_last_fix(self, session_id: str, fix: Fix) -> None:
        self.conn.execute(
            "INSERT INTO last_trusted_fix(session_id, fix) VALUES (?,?) "
            "ON CONFLICT(session_id) DO UPDATE SET fix=excluded.fix",
            (session_id, fix.model_dump_json()),
        )
        self.conn.commit()

    def add_certificate(self, signed: SignedCertificate) -> None:
        c = signed.certificate
        self.conn.execute(
            "INSERT INTO certificates(id, photo_sha256, signed) VALUES (?,?,?)",
            (c.id, c.photo_sha256, signed.model_dump_json()),
        )
        self.conn.commit()

    def get_certificate(self, cert_id: str) -> SignedCertificate | None:
        row = self.conn.execute("SELECT signed FROM certificates WHERE id=?", (cert_id,)).fetchone()
        return SignedCertificate.model_validate_json(row[0]) if row else None
