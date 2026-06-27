"""Matrix Scroll — open protocol for signed AI-assisted code provenance.

This package is the Python reference implementation of the Matrix Scroll
protocol. It exposes an Ed25519 root-of-trust abstraction with L1 emulated
software keys (default) and a typed hardware-provider path for the SSX360
reference device (NXP SE050). Hardware mode now includes a USB CDC host
transport preview plus an in-process mock path; real device signing still
depends on firmware PoC validation. Private keys are never exposed by the SDK
API.

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
    HardwareProvider,
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

__version__ = "0.3.0"

__all__ = [
    "ALGORITHM",
    "DEVICE_FILE",
    "EmulatedProvider",
    "HardwareProvider",
    "IdentityError",
    "IdentityProvider",
    "SCHEMA",
    "SIGNATURE_SCHEMA",
    "__version__",
    "device_id",
    "get_provider",
    "identity_info",
    "public_key_b64",
    "sign",
    "sign_manifest",
    "status",
    "store_dir",
    "verify",
    "verify_manifest",
]
