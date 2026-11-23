"""Ed25519 certificate signing (PyNaCl).

The signature covers the canonical JSON of the certificate (sorted keys, no
whitespace), so any verifier can recompute it byte for byte.
"""

import base64
import json
import os
from pathlib import Path

from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey

from .models import Certificate

def canonical(cert: Certificate) -> bytes:
    return json.dumps(cert.model_dump(), sort_keys=True, separators=(",", ":")).encode()


def load_or_create_key(path: Path | None = None) -> SigningKey:
    path = path or Path(os.environ.get("SIGNING_KEY_PATH", "keys/signing.key"))
    if path.exists():
        return SigningKey(path.read_bytes())
    path.parent.mkdir(parents=True, exist_ok=True)
    key = SigningKey.generate()
    path.write_bytes(bytes(key))
    path.chmod(0o600)
    return key


def b64(b: bytes) -> str:
    return base64.b64encode(b).decode()


def sign(cert: Certificate, key: SigningKey) -> str:
    return b64(key.sign(canonical(cert)).signature)


def verify(cert: Certificate, signature_b64: str, public_key_b64: str) -> bool:
    try:
        VerifyKey(base64.b64decode(public_key_b64)).verify(canonical(cert), base64.b64decode(signature_b64))
        return True
    except (BadSignatureError, ValueError):
        return False
