"""Release metadata checks for public-facing SDK links."""

import re
from pathlib import Path

import yaml


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


def test_workflows_and_sdk_messages_carry_no_killed_product_copy():
    """Matrix Scroll is the open protocol. It has no tiers, seats, or signup.

    The tier sentence rendered in the Actions UI of a public repository and in
    every SDK error a user without an API key saw. It survives a rebuild easily,
    because nobody rereads a workflow's `echo` lines, so pin it here.
    """
    surfaces = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
    surfaces += [
        ROOT / "matrixscroll" / "mcp.py",
        ROOT / "matrixscroll" / "cloud" / "client.py",
        ROOT / "docs" / "quickstart-mcp.md",
    ]
    forbidden = [
        "community tier",
        "verifications/day",
        "ssx360.com/signup",
        "ssx360.com/#pricing",
    ]
    for path in surfaces:
        text = path.read_text(encoding="utf-8").lower()
        for phrase in forbidden:
            assert phrase not in text, f"{phrase!r} found in {path.name}"


def test_step_summaries_carry_no_em_dashes():
    """House rule: no em-dash, and no en-dash used as a separator."""
    for path in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        assert "\u2014" not in text, f"em-dash in {path.name}"
        assert not re.search(r"(?<!\d)\u2013|\u2013(?!\d)", text), (
            f"en-dash separator in {path.name}"
        )


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


def test_dependabot_does_not_widen_the_incompatible_mcp_major():
    """MCP 2.x removed the FastMCP API used by the published server."""
    config = yaml.safe_load(
        (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    )
    pip_updates = [
        update
        for update in config["updates"]
        if update["package-ecosystem"] == "pip" and update["directory"] == "/"
    ]

    assert len(pip_updates) == 1
    update = pip_updates[0]
    mcp_ignores = [
        rule for rule in update["ignore"] if rule["dependency-name"] == "mcp"
    ]

    assert len(mcp_ignores) == 1
    assert ">=2.0.0.dev0" in mcp_ignores[0]["versions"]
    assert "mcp" in update["groups"]["dev-dependencies"]["exclude-patterns"]
