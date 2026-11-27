from firebase_admin import auth, firestore
from registration_validation import normalize_cpf, resolve_registration

REAL_UNITS = {"101","102","103","104","201","202","203","204","301","302","303","304","401","402","403","404","501","502","503","504","601","602"}

def eligible(cpf, email, residents):
    result = resolve_registration(cpf, residents)
    unit = result.get("unit")
    if result["status"] != "matched" or unit not in REAL_UNITS - {"204"}:
        return None
    stored = str(residents[unit].get("email") or "").strip().lower()
    return unit if stored and stored == email.strip().lower() else None

@firestore.transactional
def grant(tx, db, uid, email):
    account_ref = db.collection("users").document(uid)
    claim_ref = db.collection("registration_claims").document(uid)
    decision_ref = db.collection("registration_decisions").document(uid)
    account = account_ref.get(transaction=tx).to_dict() or {}
    claim = claim_ref.get(transaction=tx).to_dict() or {}
    if account.get("status") != "pending" or account.get("role") != "user" or account.get("email") != email or claim.get("email") != email:
        return
    if decision_ref.get(transaction=tx).exists or db.collection("registration_delete_requests").document(uid).get(transaction=tx).exists or db.collection("test_access").document(uid).get(transaction=tx).exists:
        return
    residents = {d.id:d.to_dict() for d in db.collection("residents").stream(transaction=tx)}
    test = db.collection("test_units").document("107").collection("registry").document("resident").get(transaction=tx).to_dict() or {}
    cpf = normalize_cpf(claim.get("cpf"))
    if cpf and normalize_cpf(test.get("cpf")) == cpf and not any(normalize_cpf(d.get("cpf")) == cpf for d in residents.values()):
        if str(test.get("email") or "").strip().lower() != email.strip().lower():
            return
        if email.lower() not in {"adm.isamig@gmail.com", "washington.souza@grupoisamig.com.br"}:
            return
        lock = db.collection("registration_auto_locks").document("107")
        if lock.get(transaction=tx).exists:
            return
        tx.create(lock, {"uid":uid,"createdAt":firestore.SERVER_TIMESTAMP})
        tx.create(db.collection("test_access").document(uid), {"unit":"107","status":"approved","updatedBy":"automatic_verified_existing_email","updatedAt":firestore.SERVER_TIMESTAMP})
        tx.set(db.collection("registration_review_private").document(uid), {"result":{"status":"test_matched","unit":"107"},"processedAt":firestore.SERVER_TIMESTAMP})
        return
    unit = eligible(claim.get("cpf"), email, residents)
    if not unit:
        return
    if any(d.id != uid and d.to_dict().get("status") == "approved" for d in db.collection("users").where("unit","==",unit).stream(transaction=tx)):
        return
    # Shared per-unit lock prevents concurrent automatic grants.
    lock = db.collection("registration_auto_locks").document(unit)
    if lock.get(transaction=tx).exists:
        return
    tx.create(lock, {"uid":uid,"createdAt":firestore.SERVER_TIMESTAMP})
    tx.create(decision_ref, {"decision":"approved","unit":unit,"decidedBy":"automatic_verified_existing_email","decidedAt":firestore.SERVER_TIMESTAMP})
    tx.update(account_ref, {"status":"approved","role":"resident","unit":unit})

def process_auto(db):
    for claim in db.collection("registration_claims").stream():
        try:
            user = auth.get_user(claim.id)
        except auth.UserNotFoundError:
            continue
        if user.email_verified and not user.disabled and user.email and user.email.lower() != "washington.s.souza@gmail.com":
            grant(db.transaction(), db, claim.id, user.email)
