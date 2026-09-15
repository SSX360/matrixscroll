#!/usr/bin/env node
/**
 * Structural Matrix Scroll verifier stub.
 *
 * Loads a vector JSON file and checks that required schema strings are present.
 * Full Ed25519 verification (e.g. via tweetnacl) is TODO; this path confirms
 * fixture shape and a SHA-256 checksum of the raw file bytes.
 *
 * Usage: node src/verify.mjs <path-to-vector.json>
 */

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const SIGNATURE_SCHEMA = "matrixscroll.signature.v1";

function fail(message) {
  console.error(JSON.stringify({ ok: false, error: message }));
  process.exit(2);
}

function main() {
  const path = process.argv[2];
  if (!path) {
    fail("usage: node src/verify.mjs <vector.json>");
  }
  const abs = resolve(path);
  const raw = readFileSync(abs);
  const checksum = createHash("sha256").update(raw).digest("hex");

  let doc;
  try {
    doc = JSON.parse(raw.toString("utf8"));
  } catch (err) {
    fail(`invalid JSON: ${err.message}`);
  }

  if (typeof doc !== "object" || doc === null || Array.isArray(doc)) {
    fail("document must be a JSON object");
  }

  const schema = doc.schema;
  if (typeof schema !== "string" || !schema.includes("matrixscroll")) {
    fail("missing or unexpected top-level schema string");
  }

  const block = doc.signature;
  if (!block || typeof block !== "object") {
    fail("missing signature block");
  }
  if (block.schema !== SIGNATURE_SCHEMA) {
    fail(`signature.schema must be ${SIGNATURE_SCHEMA}`);
  }
  if (typeof block.algorithm !== "string" || !block.algorithm) {
    fail("signature.algorithm missing");
  }

  // TODO: Ed25519 verify over canonical bytes (tweetnacl or Web Crypto).
  console.log(
    JSON.stringify({
      ok: true,
      structural: true,
      ed25519: "todo",
      schema,
      algorithm: block.algorithm,
      file_sha256: checksum,
    })
  );
}

main();
