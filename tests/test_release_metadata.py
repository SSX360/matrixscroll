"""Release metadata checks for public-facing SDK links."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_public_metadata_uses_stable_device_url():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert '"Reference Device" = "https://matrixscroll.com/device"' in pyproject
    assert "[SSX360](https://matrixscroll.com/device)" in readme


def test_sdk_public_docs_do_not_link_vercel_preview_urls():
    checked = [ROOT / "README.md", ROOT / "pyproject.toml", ROOT / "SPEC.md"]
    for path in checked:
        text = path.read_text(encoding="utf-8")
        assert "vercel.app" not in text, path.name