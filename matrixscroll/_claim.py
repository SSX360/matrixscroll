"""
matrixscroll claim / identity / verify --identity
Drop into the package as matrixscroll/_claim.py and wire the subcommands into the
existing argparse CLI. Ship as 0.3.0. Hard invariant: the private seed NEVER
leaves the machine — enroll proves key control by signing a server nonce locally.
Depends only on the public 0.3.0 surface: status(), sign_manifest(), verify_manifest().
"""
from __future__ import annotations
import json, os, time, webbrowser, urllib.request, urllib.error
from pathlib import Path
import matrixscroll

AUTHORITY = os.environ.get("MATRIXSCROLL_AUTHORITY_URL", "https://matrixscroll.com")
HOME = Path(os.environ.get("MATRIXSCROLL_HOME", str(Path.home() / ".matrixscroll")))
CERT_PATH = HOME / "identity_certificate.json"


def _post(path: str, body: dict) -> dict:
    req = urllib.request.Request(
        AUTHORITY + path, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise SystemExit(f"authority error {e.code}: {e.read().decode('utf-8','replace')}")


def cmd_claim(args) -> int:
    """matrixscroll claim — enroll this key and bind it to a verified identity."""
    st = matrixscroll.status()
    pub, dev = st["public_key"], st["device_id"]
    print(f"Claiming identity for {dev}")

    start = _post("/api/enroll/start", {"public_key": pub, "device_id": dev})
    nonce, cid, login_url = start["nonce"], start["challenge_id"], start["login_url"]

    # prove key control by signing the nonce LOCALLY (no seed leaves)
    signed_nonce = matrixscroll.sign_manifest({"challenge_id": cid, "nonce": nonce})

    print(f"\nOpen this URL to sign in to your provisioned SSX360 account:\n  {login_url}\n")
    if not args.no_browser:
        try: webbrowser.open(login_url)
        except Exception: pass
    input("Press Enter here AFTER you complete sign-in in the browser... ")

    for _ in range(6):  # poll while the Stripe webhook lands
        out = _post("/api/enroll/complete", {"challenge_id": cid, "signed_nonce": signed_nonce})
        if out.get("status") == "issued":
            HOME.mkdir(mode=0o700, exist_ok=True)
            CERT_PATH.write_text(json.dumps(out["certificate"], indent=2))
            sub = out["certificate"]["subject"]
            print(f"\n✓ Verified identity issued: {sub['display_name']}")
            print(f"  accounts: {', '.join(a['type']+':'+a['value'] for a in sub['verified_accounts'])}")
            print(f"  plan: {sub['plan']}   expires: {sub['expires_at']}")
            print(f"  public profile: https://matrixscroll.com/id/{dev}")
            return 0
        if out.get("status") == "pending_subscription":
            time.sleep(5); continue
        raise SystemExit(f"enrollment failed: {out.get('detail', out)}")
    raise SystemExit("subscription not active yet — run `matrixscroll claim` again once Stripe confirms.")


def cmd_identity(args) -> int:
    """matrixscroll identity — local verified-identity status. Exit 0 valid, 2 otherwise."""
    if not CERT_PATH.exists():
        print("Self-signed — identity not verified. Run: matrixscroll claim"); return 2
    cert = json.loads(CERT_PATH.read_text())
    if not matrixscroll.verify_manifest(cert):
        print("certificate signature INVALID — re-claim required"); return 2
    sub = cert["subject"]
    expired = sub["expires_at"] < time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    print(f"identity: {sub['display_name']}  ({'EXPIRED' if expired else 'valid'})")
    print(f"  device: {sub['device_id']}  plan: {sub['plan']}  expires: {sub['expires_at']}")
    return 2 if expired else 0


def resolve_identity(signature_block: dict, roots_dir: Path | None = None) -> str:
    """For `verify --identity`: resolve the signer's published cert to a human label.
    Offline-first: local cache, else the public directory."""
    dev = signature_block.get("device_id", "")
    cached = (roots_dir or HOME) / "ids" / f"{dev}.json"
    cert = None
    if cached.exists():
        cert = json.loads(cached.read_text())
    else:
        try:
            with urllib.request.urlopen(f"https://matrixscroll.com/id/{dev}.json", timeout=10) as r:
                cert = json.loads(r.read().decode("utf-8"))
        except Exception:
            return f"Self-signed — {dev} (identity not verified)"
    if cert and matrixscroll.verify_manifest(cert):
        sub = cert["subject"]
        accts = ", ".join(f"{a['type']}:{a['value']}" for a in sub["verified_accounts"])
        return f"Verified identity: {sub['display_name']} ({accts})"
    return f"Self-signed — {dev} (cert invalid)"
