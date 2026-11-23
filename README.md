# cassini-backend

Location trust and photo-evidence backend for the CASSINI hackathon (working name: Svidok).
The Android collector posts GNSS / cell / Wi-Fi evidence; this service scores how far the
location can be trusted, recovers a best-estimate position under spoofing, and issues
Ed25519-signed certificates for photos.

## Run

```sh
uv sync
uv run uvicorn cassini_backend.main:app --reload   # http://localhost:8000/docs
uv run pytest
```

Docker: `docker build -t cassini-backend . && docker run -p 8000:8000 -v cassini-data:/data cassini-backend`

## API

| Endpoint | Purpose |
|---|---|
| `POST /reports` | Collector upload every ~5 s → `green/amber/red`, best estimate, flags with a "why" |
| `POST /certificates` | Photo SHA-256 + evidence bundle → signed certificate |
| `GET /certificates/{id}` | Fetch a certificate (QR / verify link) |
| `POST /verify` | Check a certificate's signature |
| `POST /verify/{id}/photo` | Upload the original photo; recompute hash and check it |
| `GET /public-key` | Ed25519 verify key |

## Layout

- `scoring.py` — rule-based trust checks (plan §3). Thresholds are first guesses; calibrate per phone on recorded logs.
- `certs.py` — canonical JSON + Ed25519 signing.
- `eo.py` — Copernicus/APEx context lookup (`NullEO` placeholder until rasters exist).
- `db.py` — SQLite: reports, last trusted fix per session, certificates. Never stores photos.
- `tests/scenarios.py` — demo scenarios (honest Kyiv photo, Lima spoof) as synthetic reports.

## OSNMA proof of concept

`poc/osnma_poc.py` runs [OSNMAlib](https://github.com/Algafix/OSNMA) (EUPL-1.2, cloned next to this repo in
`../osnmalib` with its own venv) on a real Galileo recording three ways: honest, wrong public key, and one
satellite's ephemeris tampered in software.

```sh
git clone https://github.com/Algafix/OSNMA ../osnmalib
(cd ../osnmalib && uv venv --python 3.12 && uv pip install -r requirements.txt)
../osnmalib/.venv/bin/python poc/osnma_poc.py ../osnmalib
```

Result (23 Nov 2026): honest → 11 satellites authenticated, first authenticated fix after 110 s;
wrong key → rejected; tampered → satellite 19 drops out with 788 failed tags, the other 10 stay authenticated.

## Not yet done

- OSNMAlib wired into the API (proven standalone in `poc/`; still unproven on a phone GnssLogger recording)
- Galileo-only / GPS-only fixes from raw measurements (gnss_lib_py)
- GnssLogger log parser + replay mode
- OpenCellID / WiGLE lookups (cell and Wi-Fi positions currently arrive resolved)
- EO rasters, Play Integrity check, MinIO photo storage, H3 aggregation
