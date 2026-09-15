"""Matrix Scroll — open protocol for signed AI-assisted code provenance.

This package is the Python reference implementation of the Matrix Scroll
protocol. It exposes Ed25519 signing through a file-backed software provider
and an ``IdentityProvider`` seam so any device or HSM can plug in. An optional
post-quantum overlay defaults to ML-DSA-87; ML-KEM-1024 primitives and sealed
evidence packs support the CNSA 2.0 Category 5 track.

Quickstart:

    >>> import matrixscroll
    >>> info = matrixscroll.identity_info()
    >>> signed = matrixscroll.sign_manifest({"release": "v1.0.0"})
    >>> matrixscroll.verify_manifest(signed)
    True

See SPEC.md for the wire format and canonical encoding rules.
"""

from ._core import (
    ALGORITHM,
    DEVICE_FILE,
    SCHEMA,
    SIGNATURE_SCHEMA,
    EmulatedProvider,
    IdentityError,
    IdentityProvider,
    device_id,
    get_provider,
    identity_info,
    public_key_b64,
    sign,
    sign_manifest,
    status,
    store_dir,
    verify,
    verify_manifest,
)
from .ledger import Ledger, verify_bundle, verify_chain
from .sealed import seal_evidence_pack, unseal_evidence_pack
from .verdict import Verdict

__version__ = "0.10.0"

__all__ = [
    "ALGORITHM",
    "DEVICE_FILE",
    "EmulatedProvider",
    "IdentityError",
    "IdentityProvider",
    "Ledger",
    "SCHEMA",
    "SIGNATURE_SCHEMA",
    "Verdict",
    "__version__",
    "device_id",
    "get_provider",
    "identity_info",
    "public_key_b64",
    "seal_evidence_pack",
    "sign",
    "sign_manifest",
    "status",
    "store_dir",
    "unseal_evidence_pack",
    "verify",
    "verify_bundle",
    "verify_chain",
    "verify_manifest",
]
