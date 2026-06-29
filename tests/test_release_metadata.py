"""Release metadata checks for public-facing SDK links."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_public_metadata_uses_stable_device_url():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert '"Reference Device" = "https://ssx360.com/hardware"' in pyproject or "ssx360.com/hardware" in pyproject
    assert "[AP2 Vault Card hardware](https://ssx360.com/hardware)" in readme


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
