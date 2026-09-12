# Where Matrix Scroll fits

Matrix Scroll signs a declared authorization record at commit or action time.
It complements, rather than replaces, identity systems, source-control policy,
build provenance, artifact signing, and runtime security controls.

Compliance language on this page is evidence mapping, not a certification claim.

## Control boundaries

| Control area | Primary question | Matrix Scroll role |
| --- | --- | --- |
| Identity and access management | Who may access or change a system? | Consumes trusted-key and authorization policy; does not issue access |
| Source-control policy | Which changes may merge? | Supplies a signed record and range-verification result for policy checks |
| Build provenance | What process produced an artifact? | Supplies optional source-history evidence; does not attest the build |
| Artifact signing | Which key signed a release or image? | Separate control; Matrix Scroll records can be referenced by the release process |
| Runtime security | What code or process is executing now? | Outside protocol scope |
| Compliance assessment | Which evidence supports a control review? | Exports signed records and verification results for scoped review |

## Commit-time and artifact-time evidence

Matrix Scroll binds an envelope to a Git commit before or around push. Build
provenance and artifact-signing systems operate later, after CI has produced an
artifact. A complete software supply-chain review may use both:

1. Matrix Scroll records the declared actor class, tool, scope, and commit SHA.
2. Scroll Gate checks the selected commit range against key and policy inputs.
3. CI produces build provenance and signs the resulting artifact.
4. Reviewers compare the source-history and artifact evidence as separate
   control records.

## Signer choices

The file-backed provider is included for local use, tests, and CI. The completed
SSX360 USB signer keeps the Ed25519 private key inside an NXP SE050 secure
element and is supplied through [SSX360 contact](https://ssx360.com/contact).
Both paths produce the same public envelope format.

## Landscape, checked 12 September 2026

The tables below compare shipped behaviour, with a version and a date for every
row. Matrix Scroll's column names release `0.8.0` features only; anything
planned lives in [`CRYPTO_ROADMAP.md`](CRYPTO_ROADMAP.md) and
[`ROADMAP_2026-07.md`](ROADMAP_2026-07.md) under a Shipping now / In progress /
Not label. Sources are numbered at the end of the page.

### Signed records of who acted

| Tool (version, date) | What it signs | Names the acting agent | Range or sequence check | Verifies offline | Post-quantum signature option | Hardware key path | Licence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Matrix Scroll 0.8.0 (September 2026) | Commit envelopes, action records, MCP tool-surface manifests, agent traces | Yes: `actor_type` is `human`, `agent` or `ci`, with a required `tool` field [S1] | Scroll Gate verifies every commit in `base..head` and fails closed on an empty range (`allow_empty` opts out) [S1] | Yes, by default; no log lookup [S1] | ML-DSA-44/65/87 and SLH-DSA-SHA2 overlay through liboqs; `ml-dsa-87` default for new software keys; NIST ACVP sample vectors in the test suite [S1] | SSX360 USB signer, NXP SE050, Ed25519 only, supplied by direct inquiry [S1] | Apache-2.0; spec and vectors CC0 1.0 |
| Sigstore cosign 3.1.3 (6 August 2026) | OCI images, blobs, DSSE attestations | No; identity is the OIDC subject or the key [S2] | No | Yes, from a bundle with a trusted root [S3] | `ML_DSA_44/65/87` are experimental entries in protobuf-specs for private deployments; the public instance issues ECDSA, Ed25519 and RSA [S4] | PIV and PKCS#11 tokens (ECDSA P-256) [S5] | Apache-2.0 |
| Sigstore gitsign 0.17.1 (5 August 2026) | Git commits and tags with short-lived Fulcio certificates | No | No | Default verification queries Rekor; offline mode is documented as experimental [S6] | None | None (ephemeral keys) | Apache-2.0 |
| GitHub Artifact Attestations (GA 25 June 2024; SLSA Build L3 20 January 2026) | Build provenance and SBOM for artifacts | No; the workflow is the identity [S7] | No | `gh attestation verify --bundle` with a downloaded trusted root [S8] | Not stated | None | GitHub service |
| gittuf 0.16.0 (4 September 2026; OpenSSF incubating, beta) | Reference state log and policy metadata for a Git repository | No | Hash-chained log of reference updates, verifiable from any clone [S9] | Yes | None | SSH and GPG keys as the underlying signers | Apache-2.0 |
| Git commit signatures on GitHub and GitLab (GPG, SSH, S/MIME) | Commit objects | No; GitHub's Copilot cloud agent signs with a GitHub-held key and adds an `Agent-Logs-Url` trailer (3 April 2026) [S10] | No | Yes, with the public keys | OpenSSH 10.4 (6 July 2026) adds an experimental `mldsa44-ed25519` key type that neither forge verifies [S11] | `sk-*` security keys, OpenPGP cards | Git: GPL-2.0 |

### MCP tool-surface integrity

| Tool (version, date) | Method | Signed baseline | Drift detection | Runs offline |
| --- | --- | --- | --- | --- |
| Matrix Scroll `matrixscroll mcp scan`, `sign`, `verify` (0.6.0 onward; 0.8.0) | Manifest of tool names, descriptions and input schemas, signed with Ed25519 | Yes | `verify --baseline` exits `2` on a changed surface or an invalid signature [S1] | Yes |
| MCP specification revision 2026-07-28 | Protocol text; `tools/list` is deterministic, tool annotations are hints | No signing of tool definitions; SEP-1766 proposes SHA-256 digest pinning (open since November 2025) [S12] | Client-defined | n/a |
| Snyk Agent Scan 0.6.3 (10 September 2026; formerly mcp-scan) | Prompt-injection and tool-poisoning detection through the Snyk API; local state file | No | Heuristic [S13] | Needs the API |
| Cisco AI Defense MCP Scanner | YARA rules, LLM judgement, behavioural code analysis | No | Heuristic [S14] | Partly |
| Trail of Bits mcp-context-protector | Trust-on-first-use pinning of instructions, descriptions and schemas | No (unsigned pins) | Blocks on change [S15] | Yes |
| MCPTrust (no tagged release) | `mcp-lock.json` signed with Ed25519 or Sigstore keyless; CEL policy | Yes | Fails CI on drift [S16] | Yes |
| ToolHive (Stacklok) | Provenance of server images, tool filtering, OpenTelemetry audit logging | Image provenance only | Not for the live tool surface [S17] | Partly |

A signed manifest tells you that the surface you approved is the surface you
are running. It does not tell you whether the approved descriptions were safe.
Run a scanner on the baseline once and let the signature hold it still.

### Signed records of agent actions, 2025-2026

| Project (version, date) | Record | Signature | Chain | Notes |
| --- | --- | --- | --- | --- |
| Matrix Scroll 0.8.0 | Action records and commit envelopes with `actor_type`, `tool`, scope and commit SHA; signed agent traces | Ed25519, optional ML-DSA-87 or SLH-DSA overlay | Range verification over Git history | Offline verifier, CI gate, MCP manifests and a hardware signer in one SDK [S1] |
| Asqav 0.10.10 (5 September 2026) | Compliance receipts for agent actions | ML-DSA-65 with RFC 3161 timestamps | Hash chain | Elastic License 2.0; individual IETF draft (August 2026) [S18] |
| Vaara Receipt draft-07 (12 August 2026) | Paired authorization and execution receipts | ES256 default, ML-DSA-65 option | JCS-recomputable | Individual IETF draft [S19] |
| AIVS (SwarmSync) | Proof bundles with a standalone verifier | Ed25519 | SHA-256 chain | W3C community group opened 5 April 2026 [S20] |
| Phionyx AIREP 0.2.0-beta.1 (9 September 2026) | Runtime evidence envelopes | Ed25519 | Hash chain | AGPL-3.0 with dual licensing [S21] |
| Microsoft Agent Governance Toolkit (public preview) | Audit log entries | HMAC (symmetric; verification needs the key) | Merkle chain | MIT [S22] |
| GitHub Copilot coding agent audit log | `actor_is_agent`, `agent_session_id`, initiating user | None documented | None | The clearest acting-agent field in a mainstream product [S23] |
| IETF SCITT architecture, RFC 9943 (30 June 2026) | Signed statements on append-only logs with receipts | COSE | Transparency log | The standards-track model for receipts of this kind [S24] |

Matrix Scroll puts commit-time Git binding, MCP manifests, a fail-closed CI
gate, a hardware Ed25519 path and the Category 5 overlay in one Apache-2.0
package. Asqav and Vaara specify ML-DSA-65 and RFC 3161 timestamps at the
receipt-format level; Matrix Scroll has no timestamp-authority integration and
publishes to Rekor only through the dry-run bridge in `envelope-publish-rekor`.

### Regulatory context

EU AI Act Article 12 asks providers of high-risk systems for automatic event
logging over the system's lifetime; after the Digital Omnibus on AI (in force
27 July 2026) the Annex III obligations apply from 2 December 2027 [S25]. The
OWASP Top 10 for Agentic Applications (9 December 2025) asks for immutable logs
of tool calls and delegations under ASI10 [S26]. The NIST NCCoE project on
identity and authorization of software agents published its concept paper on
5 February 2026 and is reviewing comments [S27]. A signed, offline-verifiable
record is one way to produce the evidence those texts describe. This is evidence
mapping, not a certification claim, and none of those texts requires
cryptographic signing.

## What Matrix Scroll does not claim

- It is one of several 2025-2026 projects that sign agent action records; it
  does not claim to be the first or the only one.
- The PQC overlay implements FIPS 204 and FIPS 205 algorithms through liboqs,
  which the Open Quantum Safe project does not recommend for production use.
  The ACVP tests show algorithm correctness on NIST sample vectors; they are not
  a CAVP certificate or a CMVP validation.
- The SSX360 USB signer signs with Ed25519 only. NXP's SE050 and SE051 data
  sheets list no post-quantum algorithm, so any ML-DSA signature is produced in
  software.
- Records are tamper-evident. A signer that controls its own key can omit or
  alter an event before signing it; the protocol detects changes made after
  signing.
- A signed MCP manifest detects drift from an approved baseline; it does not
  judge whether the baseline was malicious.
- GitHub and GitLab show a verified badge for GPG, SSH and S/MIME commit
  signatures only. They do not verify Matrix Scroll envelopes or ML-DSA
  signatures.
- `formal/tla/` holds TLA+ models of the canonical-bytes, dual-signature and
  gate rules with TLC configurations. They check the design; they do not verify
  the Python implementation.
- Matrix Scroll is at release 0.8.0 with a prototype hardware signer supplied by
  direct inquiry. Sigstore, gittuf and the vendor identity products above have
  larger deployments.

## Limits

- A valid envelope proves integrity and key possession, not authorization to
  use the key.
- Scroll Gate does not replace branch protection or reviewer approval.
- Matrix Scroll does not establish a SLSA level or certify compliance.
- Hardware custody, trusted-key registration, revocation, and offboarding are
  deployment responsibilities.

For protocol details, read [`SPEC.md`](../SPEC.md). For an implementation path,
start with [`FIVE_MINUTES.md`](FIVE_MINUTES.md).

## Sources

- [S1] This repository at release 0.8.0: `matrixscroll/gate.py` (`verify_range`), `schemas/commit-envelope.v1.json` and `schemas/action-envelope.v1.json` (`actor_type`, `tool`), `matrixscroll/mcp_core.py`, `docs/CRYPTO_ROADMAP.md`, `vectors/acvp-sigver-fips204-fips205.json`, `docs/hardware-provider.md`.
- [S2] cosign v3.1.3 release notes, 6 August 2026: https://github.com/sigstore/cosign/releases/tag/v3.1.3
- [S3] Sigstore verification documentation (bundle verification): https://docs.sigstore.dev/cosign/verifying/verify/
- [S4] Sigstore protobuf-specs, `sigstore_common.proto` (experimental ML-DSA entries): https://github.com/sigstore/protobuf-specs/blob/main/protos/sigstore_common.proto ; Sigstore post-quantum post, 6 June 2025: https://blog.sigstore.dev/post-quantum-2025/
- [S5] Sigstore hardware token documentation: https://docs.sigstore.dev/cosign/key_management/hardware-based-tokens/
- [S6] gitsign README and v0.17.1 release, 5 August 2026: https://github.com/sigstore/gitsign
- [S7] GitHub Artifact Attestations concepts: https://docs.github.com/en/actions/concepts/security/artifact-attestations ; changelog, 20 January 2026: https://github.blog/changelog/2026-01-20-strengthen-your-supply-chain-with-code-to-cloud-traceability-and-slsa-build-level-3-security/
- [S8] Verifying attestations offline: https://docs.github.com/actions/security-for-github-actions/using-artifact-attestations/verifying-attestations-offline
- [S9] gittuf design document and v0.16.0 release, 4 September 2026: https://github.com/gittuf/gittuf
- [S10] GitHub changelog, 3 April 2026 (Copilot cloud agent signs its commits): https://github.blog/changelog/2026-04-03-copilot-cloud-agent-signs-its-commits/ ; 20 March 2026 (`Agent-Logs-Url`): https://github.blog/changelog/2026-03-20-trace-any-copilot-coding-agent-commit-to-its-session-logs/
- [S11] OpenSSH 10.4 release notes, 6 July 2026: https://www.openssh.org/txt/release-10.4 ; GitHub supported key types: https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent
- [S12] MCP specification changelog, revision 2026-07-28: https://modelcontextprotocol.io/specification/2026-07-28/changelog ; SEP-1766: https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1766
- [S13] snyk-agent-scan 0.6.3 on PyPI, 10 September 2026: https://pypi.org/project/snyk-agent-scan/ ; Invariant Labs tool-poisoning disclosure, 1 April 2025: https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks
- [S14] Cisco AI Defense MCP Scanner: https://github.com/cisco-ai-defense/mcp-scanner
- [S15] Trail of Bits mcp-context-protector: https://github.com/trailofbits/mcp-context-protector
- [S16] MCPTrust: https://github.com/mcptrust/mcptrust
- [S17] ToolHive registry criteria: https://docs.stacklok.com/toolhive/concepts/registry-criteria
- [S18] Asqav on PyPI, 0.10.10, 5 September 2026: https://pypi.org/project/asqav/ ; draft-marques-asqav-compliance-receipts-08, 31 August 2026: https://datatracker.ietf.org/doc/html/draft-marques-asqav-compliance-receipts-08
- [S19] draft-sirkkavaara-vaara-receipt-07, 12 August 2026: https://datatracker.ietf.org/doc/draft-sirkkavaara-vaara-receipt/07/
- [S20] AIVS specification and W3C community group: https://github.com/swarmsync-ai/aivs-spec ; https://www.w3.org/community/aivs/
- [S21] Phionyx AIREP adapter, 0.2.0-beta.1, 9 September 2026: https://github.com/halvrenofviryel/phionyx-openai-agents
- [S22] Microsoft Agent Governance Toolkit, audit and compliance tutorial: https://microsoft.github.io/agent-governance-toolkit/tutorials/04-audit-and-compliance/
- [S23] GitHub agentic audit log events: https://docs.github.com/en/copilot/reference/agentic-audit-log-events
- [S24] RFC 9943, SCITT architecture, 30 June 2026: https://www.rfc-editor.org/info/rfc9943
- [S25] EU AI Act Article 12: https://artificialintelligenceact.eu/article/12/ ; Digital Omnibus on AI in force 27 July 2026: https://www.lewissilkin.com/insights/2026/07/27/the-digital-omnibus-on-ai-enters-into-force-today-102nedo
- [S26] OWASP Top 10 for Agentic Applications 2026, 9 December 2025: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
- [S27] NIST NCCoE, Software and AI Agent Identity and Authorization: https://www.nccoe.nist.gov/projects/software-and-ai-agent-identity-and-authorization
