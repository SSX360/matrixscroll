"""Matrix Scroll protocol constants."""

from __future__ import annotations

SCHEMA = "matrixscroll.identity.v1"
SIGNATURE_SCHEMA = "matrixscroll.signature.v1"
PQC_SIGNATURE_SCHEMA = "matrixscroll.pqc_signature.v1"
PQC_IDENTITY_SCHEMA = "matrixscroll.pqc_identity.v1"
ALGORITHM = "ed25519"

PQC_ALGORITHMS: tuple[str, ...] = (
    "ml-dsa-44",
    "ml-dsa-65",
    "ml-dsa-87",
    "slh-dsa-sha2-128s",
    "slh-dsa-sha2-128f",
)
DEFAULT_PQC_ALGORITHM = "ml-dsa-65"
PQC_ENV_VAR = "MATRIXSCROLL_PQC"

DEVICE_FILE = "device.json"
PQC_DIR_NAME = "pqc"

SEED_LEN = 32
DIR_MODE = 0o700
FILE_MODE = 0o600
