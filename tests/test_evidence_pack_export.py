"""Evidence pack export: signature safety and schema identity.

Two invariants live here.

First, ``ssx360 ledger export`` is a verification tool, so it must never change
a document it might later be asked to verify. The hosted evidence pack arrives
as a response body from ssx360.com. If that body ever carries a signature, the
framework annotation step has to leave its canonical bytes alone, because
``canonical_bytes`` covers every top-level key except ``signature`` and
``pqc_signatures``. Adding ``framework`` next to a signature breaks it.

Second, the ``schema`` value the exporter stamps has to name a schema that
ships in the package and describes the document.
"""

from __future__ import annotations

import copy
import io
import json
import os
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from matrixscroll import ssx360_cli
from matrixscroll._schemas import schema_path
from matrixscroll.canonical import canonical_bytes
from matrixscroll.manifest import sign_manifest, verify_manifest

HOSTED_ENV = {"SSX360_API_KEY": "test-key"}


def _signed_hosted_pack() -> dict:
    """A hosted response body carrying an Ed25519 signature over itself."""
    return sign_manifest(
        {
            "schema": ssx360_cli.EVIDENCE_PACK_SCHEMA,
            "ok": True,
            "source": "hosted",
            "exported_at": "2026-08-05T00:00:00Z",
            "envelopes": [{"sha": "a" * 40, "verified": True}],
        }
    )


def _exported_signed_document(exported: dict) -> dict:
    """Pull the server's document back out of whatever the exporter wrote.

    Written to find the document wherever the exporter chose to put it, so the
    assertion that follows is about the signature rather than about a key name.
    """
    return exported.get("evidence_pack", exported)


def _run_hosted_export(server_response: dict, out_path: Path) -> dict:
    served = copy.deepcopy(server_response)
    with mock.patch.dict(os.environ, HOSTED_ENV, clear=True), mock.patch(
        "matrixscroll.cloud.audit_export", return_value=served
    ):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = ssx360_cli.ledger_main(["--export", "SOC2", "-o", str(out_path)])
    assert rc == 0, buf.getvalue()
    return json.loads(out_path.read_text(encoding="utf-8"))


class HostedExportSignatureTests(unittest.TestCase):
    def test_signed_hosted_pack_still_verifies_after_export(self):
        signed = _signed_hosted_pack()
        self.assertTrue(verify_manifest(signed), "fixture is not signed correctly")

        with TemporaryDirectory() as tmp:
            exported = _run_hosted_export(signed, Path(tmp) / "pack.json")

        document = _exported_signed_document(exported)
        self.assertTrue(
            verify_manifest(document),
            "the framework annotation step invalidated the signature the server sent",
        )

    def test_signed_hosted_pack_keeps_its_canonical_bytes(self):
        signed = _signed_hosted_pack()

        with TemporaryDirectory() as tmp:
            exported = _run_hosted_export(signed, Path(tmp) / "pack.json")

        document = _exported_signed_document(exported)
        self.assertEqual(
            canonical_bytes(signed),
            canonical_bytes(document),
            "the exported document is not byte-identical to the one the server signed",
        )

    def test_framework_annotation_reaches_the_exported_file(self):
        """The annotation is the point of the command. It has to survive too."""
        signed = _signed_hosted_pack()

        with TemporaryDirectory() as tmp:
            exported = _run_hosted_export(signed, Path(tmp) / "pack.json")

        self.assertEqual(exported["framework"], "SOC2")
        self.assertEqual(exported["framework_mapping"]["id"], "soc2-type-ii")
        self.assertIn("does not constitute certification", exported["disclaimer"])

    def test_annotation_does_not_mutate_the_response_object(self):
        """Even unsigned, the response object the caller handed over stays intact."""
        response = {"ok": True, "schema": "hosted.thing.v1", "records": []}
        before = copy.deepcopy(response)

        annotated = ssx360_cli._annotate(response, ssx360_cli._framework_annotation("SOC2"))

        self.assertEqual(response, before)
        self.assertIsNot(annotated, response)

    def test_hosted_check_does_not_mutate_the_summary_it_received(self):
        summary = {"ok": True, "verified_count": 2, "total": 2}
        before = copy.deepcopy(summary)
        with mock.patch.dict(os.environ, HOSTED_ENV, clear=True), mock.patch(
            "matrixscroll.ssx360_cli._resolve_pr_refs", return_value=("abc123", "def456")
        ), mock.patch(
            "matrixscroll.ssx360_cli._collect_commits_for_hosted",
            return_value=[{"sha": "a" * 40}],
        ), mock.patch(
            "matrixscroll.cloud.verify_range", return_value=summary
        ):
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = ssx360_cli.main(["check", "--pr", "7"])

        self.assertEqual(rc, 0, buf.getvalue())
        self.assertEqual(summary, before, "the hosted verify response was mutated in place")
        self.assertEqual(json.loads(buf.getvalue())["pr"], 7)

    def test_signed_hosted_summary_survives_the_pr_annotation(self):
        summary = sign_manifest({"ok": True, "verified_count": 1, "total": 1})
        with mock.patch.dict(os.environ, HOSTED_ENV, clear=True), mock.patch(
            "matrixscroll.ssx360_cli._resolve_pr_refs", return_value=("abc123", "def456")
        ), mock.patch(
            "matrixscroll.ssx360_cli._collect_commits_for_hosted",
            return_value=[{"sha": "a" * 40}],
        ), mock.patch(
            "matrixscroll.cloud.verify_range", return_value=copy.deepcopy(summary)
        ):
            buf = io.StringIO()
            with redirect_stdout(buf):
                ssx360_cli.main(["check", "--pr", "7"])

        printed = json.loads(buf.getvalue())
        self.assertTrue(
            verify_manifest(printed.get("result", printed)),
            "attaching the PR number invalidated the signature the server sent",
        )


class LocalExportShapeTests(unittest.TestCase):
    """The local wrapper is built here, so its 0.6.2 shape has to hold."""

    @mock.patch.dict("os.environ", {}, clear=True)
    @mock.patch("matrixscroll.gate.export_envelope_bundle")
    def test_local_export_keeps_its_flat_top_level_keys(self, export_mock):
        export_mock.return_value = {"bundle": "out", "count": 1}
        with TemporaryDirectory() as tmp:
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = ssx360_cli.ledger_main(["--export", "SOC2", "-o", tmp])
            self.assertEqual(rc, 0)
            manifest = Path(tmp) / "evidence-pack-soc2.json"
            pack = json.loads(manifest.read_text(encoding="utf-8"))

        self.assertEqual(
            sorted(pack),
            [
                "bundle",
                "disclaimer",
                "exported_at",
                "framework",
                "framework_mapping",
                "ok",
                "schema",
                "source",
            ],
        )
        self.assertEqual(pack["source"], "local")


class EvidencePackSchemaTests(unittest.TestCase):
    def test_emitted_schema_id_matches_the_shipped_schema_file(self):
        schema = json.loads(
            schema_path("ssx360.evidence-pack.v1.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            schema["properties"]["schema"]["const"],
            ssx360_cli.EVIDENCE_PACK_SCHEMA,
        )

    def test_local_export_carries_every_key_the_schema_requires(self):
        schema = json.loads(
            schema_path("ssx360.evidence-pack.v1.json").read_text(encoding="utf-8")
        )
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch(
            "matrixscroll.gate.export_envelope_bundle",
            return_value={"bundle": "out", "count": 1},
        ):
            with TemporaryDirectory() as tmp:
                buf = io.StringIO()
                with redirect_stdout(buf):
                    ssx360_cli.ledger_main(["--export", "ISO27001", "-o", tmp])
                pack = json.loads(
                    (Path(tmp) / "evidence-pack-iso27001.json").read_text(encoding="utf-8")
                )

        for key in schema["required"]:
            self.assertIn(key, pack)
        self.assertEqual(pack["schema"], schema["properties"]["schema"]["const"])

    def test_every_shipped_schema_resolves_through_the_package(self):
        """Guards the packaging fix: these files have to be findable at runtime."""
        for name in (
            "commit-envelope.v1.json",
            "action-envelope.v1.json",
            "ssx360.mcp-manifest.v1.json",
            "ssx360.evidence-pack.v1.json",
        ):
            self.assertTrue(schema_path(name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
