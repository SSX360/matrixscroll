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
    "slh-dsa-sha2-256s",
    "slh-dsa-sha2-256f",
)
# Default is ML-DSA-87 (FIPS 204 Category 5). That matches the CNSA 2.0
# signature parameter set NSA publishes for National Security Systems.
# Shipping this default is parameter-set readiness through liboqs, not CNSA
# certification, FIPS CMVP validation, or NSA approval. Callers may still
# select ml-dsa-44 or ml-dsa-65 explicitly.
DEFAULT_PQC_ALGORITHM = "ml-dsa-87"
# Preferred algorithm when a deployment asks for CNSA 2.0 Category 5 signature
# alignment. Identical to DEFAULT_PQC_ALGORITHM today; kept named so policy and
# docs can reference the intent without hard-coding a string.
CNSA_PREFERRED_PQC_ALGORITHM = "ml-dsa-87"
PQC_ENV_VAR = "MATRIXSCROLL_PQC"

DEVICE_FILE = "device.json"
PQC_DIR_NAME = "pqc"

SEED_LEN = 32
DIR_MODE = 0o700
FILE_MODE = 0o600
