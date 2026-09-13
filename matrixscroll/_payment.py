import datetime
from . import sign_manifest, status

def sign_payment(tx_id, amount, currency, merchant, payment_type, identifier_hash, key_path=None):
    """
    Constructs and signs a matrixscroll.agent_payment.v1 attestation.
    """
    auth = status(key_path)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    # Format to match milliseconds-free Zulu format if needed
    if "." in now:
        now = now.split(".")[0] + "Z"
    else:
        now = now.replace("+00:00", "Z")

    attestation = {
        "schema": "matrixscroll.agent_payment.v1",
        "transaction_id": tx_id,
        "amount": float(amount),
        "currency": currency,
        "merchant": merchant,
        "payment_method": {
            "type": payment_type,
            "identifier_hash": identifier_hash
        },
        "agent_device_id": auth["device_id"],
        "timestamp": now
    }

    signed = sign_manifest(attestation, key_path)
    return signed
