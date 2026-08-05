"""The shipped package sells nothing.

Matrix Scroll is the open protocol and stays free. SSX360 sells assessments,
and a paid mechanism inside the protocol client would let a vendor bill the
same party it audits. These checks read the installed module tree rather than
the docs, because the wheel is what a user actually receives.
"""

import ast
from pathlib import Path

from matrixscroll.cli import build_parser


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "matrixscroll"

# Every phrase here shipped in matrixscroll 0.6.2 through the `claim`
# enrollment flow, which polled an authority endpoint for a Stripe
# subscription before it would issue an identity certificate.
FORBIDDEN_SOURCE_PHRASES = (
    "stripe",
    "pending_subscription",
    "subscription",
    "ssx360.com/signup",
    "ssx360.com/#pricing",
    "per seat",
)


def _python_sources() -> list[Path]:
    return sorted(p for p in PACKAGE.rglob("*.py") if "__pycache__" not in p.parts)


def test_no_module_carries_monetization_language():
    for path in _python_sources():
        text = path.read_text(encoding="utf-8").lower()
        for phrase in FORBIDDEN_SOURCE_PHRASES:
            assert phrase not in text, f"{phrase!r} found in matrixscroll/{path.relative_to(PACKAGE)}"


def test_cli_exposes_no_enrollment_subcommands():
    """`claim` opened a browser to a paid sign-up and polled a Stripe webhook.

    `identity` and `verify --identity` only ever resolved certificates that
    the same flow issued, so they outlive their issuer with nothing to read.
    """
    parser = build_parser()
    actions = [a for a in parser._actions if getattr(a, "choices", None) and hasattr(a, "_name_parser_map")]
    assert actions, "expected a subparsers action on the matrixscroll parser"
    commands = set(actions[0].choices)
    assert "claim" not in commands
    assert "identity" not in commands

    for subcommand in ("verify", "envelope-verify"):
        flags = {opt for action in actions[0].choices[subcommand]._actions for opt in action.option_strings}
        assert "--identity" not in flags, f"--identity still on `matrixscroll {subcommand}`"


def test_no_module_imports_the_removed_claim_module():
    for path in _python_sources():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").endswith("_claim"):
                raise AssertionError(f"matrixscroll/{path.relative_to(PACKAGE)} imports _claim")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.endswith("_claim"), path.name
