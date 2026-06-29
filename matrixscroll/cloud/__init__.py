"""SSX360 hosted platform client for Matrix Scroll network features."""

from matrixscroll.cloud.client import (
    CloudAuthError,
    DOCS_URL,
    SIGNUP_URL,
    audit_export,
    list_envelopes,
    verify_range,
)

__all__ = [
    "CloudAuthError",
    "DOCS_URL",
    "SIGNUP_URL",
    "audit_export",
    "list_envelopes",
    "verify_range",
]
