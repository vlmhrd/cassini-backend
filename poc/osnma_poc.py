"""OSNMA proof of concept: does Galileo authentication accept real data and reject fakes?

Runs OSNMAlib on a real Galileo recording (Septentrio SBF shipped with OSNMAlib) three ways:
  honest      - unmodified recording, official public key 2       -> expect authentication
  wrong_key   - same recording, outdated public key 1             -> expect KROOT rejected
  tampered    - ephemeris bits of one satellite altered in software -> expect that satellite's tags FAILED

Software-only: no signals are transmitted. Usage (with OSNMAlib's venv):
  ../osnmalib/.venv/bin/python poc/osnma_poc.py ../osnmalib
"""

import io
import logging
import re
import sys
import tempfile
from collections import Counter
from contextlib import redirect_stdout
from pathlib import Path

osnmalib = Path(sys.argv[1] if len(sys.argv) > 1 else "../osnmalib").resolve()
sys.path.insert(0, str(osnmalib))

from osnma.input_formats.input_sbf import SBF  # noqa: E402
from osnma.receiver.receiver import OSNMAReceiver  # noqa: E402

RUN_DIR = osnmalib / "custom_run"
RECORDING = RUN_DIR / "current_config.sbf"
TAMPER_SVID = 19


class Tamper(SBF):
    """Flip bits inside I/NAV ephemeris words (types 1-4) of one satellite, like forged orbit data."""

    def __next__(self):
        page = super().__next__()
        bits = page.nav_bits
        word_type = bits[2:8].uint  # even page: [even/odd][page type][word type x6][data...]
        if page.svid == TAMPER_SVID and 1 <= word_type <= 4:
            bits.invert(range(30, 34))
        return page


def run(label: str, pubkey: str, reader_cls=SBF) -> dict:
    out_dir = Path(tempfile.mkdtemp(prefix=f"osnma_{label}_"))
    for f in ("OSNMA_MerkleTree.xml", pubkey):
        (out_dir / f).write_bytes((RUN_DIR / f).read_bytes())
    config = {
        "exec_path": str(out_dir), "merkle_name": "OSNMA_MerkleTree.xml", "pubk_name": pubkey, "kroot_name": "",
        "TS": 30, "do_mack_partial_extraction": True, "do_tesla_key_regen": True,
        "do_reed_solomon_recovery": True, "do_cop_link_optimization": False, "do_dual_frequency": False,
        "stop_at_faf": False,
    }
    log = io.StringIO()
    handler = logging.StreamHandler(log)
    logging.getLogger().addHandler(handler)
    with redirect_stdout(log):
        OSNMAReceiver(reader_cls(str(RECORDING)), config).start()
    logging.getLogger().removeHandler(handler)
    text = re.sub(r"\x1b\[[0-9;]*m", "", log.getvalue() + "".join(p.read_text() for p in out_dir.rglob("*.log")))

    auth_sats = Counter(re.findall(r"AUTHENTICATED: ADKD 00 - Satellite (\d+)", text))
    failed_sats = Counter(re.findall(r"Tag FAILED\s*\n\s*\((\d+), \d+\)", text))
    ttfaf = re.search(r"TTFAF (\d+) seconds", text)
    return {
        "kroot": "AUTHENTICATED" if re.search(r"KROOT[^\n]*\n\s*AUTHENTICATED", text)
        else "REJECTED(key)" if "Problem with the Public Key" in text
        else "FAILED" if re.search(r"KROOT[^\n]*\n\s*FAILED", text) else "not verified",
        "ttfaf_s": int(ttfaf.group(1)) if ttfaf else None,
        "sats_authenticated": sorted(int(s) for s in auth_sats),
        "tag_failures": sum(failed_sats.values()),
        "sats_failed": sorted(int(s) for s in failed_sats),
    }


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    cases = [("honest", "OSNMA_PublicKey_2.xml", SBF),
             ("wrong_key", "OSNMA_PublicKey_1.xml", SBF),
             ("tampered", "OSNMA_PublicKey_2.xml", Tamper)]
    for label, key, reader in cases:
        r = run(label, key, reader)
        print(f"{label:10} KROOT={r['kroot']:13} TTFAF={str(r['ttfaf_s']) + 's' if r['ttfaf_s'] else '-':5} "
              f"authenticated sats={r['sats_authenticated']}  tag failures={r['tag_failures']} on sats {r['sats_failed']}")
