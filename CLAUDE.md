# cassini-backend

Backend for a CASSINI hackathon project (working name Svidok; final name undecided): proves where/when a
damage photo was taken even under GPS spoofing, using Galileo OSNMA, GPS/Galileo/cell/Wi-Fi cross-checks
and Copernicus context. Hackathon: Fri 27 Nov 2026 18:00 → Sun 29 Nov, pitch Sun 15:00.

- Python 3.12, uv, FastAPI, SQLite, PyNaCl. Run tests with `uv run pytest`.
- Keep detection rules simple and explainable: every flag carries a human-readable `why`.
- Never add code that transmits GNSS signals or locates/triangulates interference sources.
  Attacks are simulated on recorded logs only.
- Photos are never stored by this service; only hashes, certificates and evidence bundles.
- Certificates sign canonical JSON (sorted keys, compact separators). Changing `Certificate` fields
  invalidates the format: keep it deliberate.
