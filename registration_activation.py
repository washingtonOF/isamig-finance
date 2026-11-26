"""Server-side activation primitives; never expose resident registry publicly."""
import hashlib
import secrets
import hmac
from datetime import datetime, timezone, timedelta
from registration_validation import normalize_cpf, resolve_registration

def issue_activation(cpf, residents, now=None):
    now = now or datetime.now(timezone.utc)
    result = resolve_registration(cpf, residents)
    if result["status"] != "matched":
        raise ValueError("Registration requires manual review")
    token = secrets.token_urlsafe(24)
    return token, {
        "tokenHash": hashlib.sha256(token.encode()).hexdigest(),
        "cpf": normalize_cpf(cpf),
        "unit": result["unit"],
        "expiresAt": now + timedelta(hours=48),
        "used": False,
    }

def verify_activation(cpf, token, record, residents, now=None):
    now = now or datetime.now(timezone.utc)
    if not isinstance(token, str) or len(token) != 32 or not record:
        return None
    if record.get("used") is not False or record["expiresAt"] <= now:
        return None
    if not hmac.compare_digest(hashlib.sha256(token.encode()).hexdigest(), record["tokenHash"]):
        return None
    normalized = normalize_cpf(cpf)
    if not normalized or normalized != record["cpf"]:
        return None
    result = resolve_registration(normalized, residents)
    if result["status"] != "matched" or result["unit"] != record["unit"]:
        return None
    return {"unit": result["unit"], "masked_name": result["masked_name"], "masked_cpf": "***.***.***-" + normalized[-2:]}

# Caller must consume the token in a trusted atomic transaction before
# granting any registration capability. Verification alone grants no access.
