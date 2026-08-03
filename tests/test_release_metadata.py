"""Release metadata checks for public-facing SDK links."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_public_metadata_uses_stable_device_url():
    """Public links must resolve directly, not through a redirect or to a dead page.

    This test used to pin `ssx360.com/hardware` and `matrixscroll.com/compare`.
    Both were retired, so the assertions were holding the metadata on two URLs
    that no longer resolved. Pin the properties instead of the literals: the
    hardware reference points at the status doc in this repo, and the protocol
    surfaces are addressed on matrixscroll.com with their canonical paths.
    """
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "docs/hardware-provider.md" in pyproject
    assert "matrixscroll.com/docs/" in pyproject
    assert "matrixscroll.com/spec/" in pyproject
    assert "matrixscroll.com/verify/" in pyproject
    assert "matrixscroll.com/docs/" in readme

    # Retired surfaces. Linking them again would send a reader to a redirect.
    for gone in ("ssx360.com/hardware", "ssx360.com/enterprise", "ssx360.com/signup"):
        assert gone not in pyproject, gone
        assert gone not in readme, gone
    for gone in ("matrixscroll.com/compare", "matrixscroll.com/ecosystem", "matrixscroll.com/roadmap"):
        assert gone not in readme, gone

    assert "[AP2 Vault Card hardware]" not in readme


def test_sdk_public_docs_do_not_link_vercel_preview_urls():
    checked = [ROOT / "README.md", ROOT / "pyproject.toml", ROOT / "SPEC.md"]
    for path in checked:
        text = path.read_text(encoding="utf-8")
        assert "vercel.app" not in text, path.name


def test_pypi_metadata_does_not_overclaim_hardware_availability():
    checked = [
        ROOT / "README.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "pyproject.toml",
        ROOT / "matrixscroll" / "__init__.py",
        ROOT / "matrixscroll" / "_core.py",
    ]
    forbidden = [
        "hardware-signed",
        "sealed in a hardware root",
        "keys never leave the provider",
    ]
    for path in checked:
        text = path.read_text(encoding="utf-8").lower()
        for phrase in forbidden:
            assert phrase not in text, f"{phrase!r} found in {path.name}"
