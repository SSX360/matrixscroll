"""Matrix Scroll — open protocol for signed AI-assisted code provenance.

This package is the Python reference implementation of the Matrix Scroll
protocol. It exposes Ed25519 signing through a file-backed software provider or
the SSX360 USB signer with an NXP SE050 secure element. The hardware provider
uses USB CDC, and its private key remains inside the secure element. The SDK
also includes an in-process hardware mock for development and CI.

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

__version__ = "0.6.4"

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
