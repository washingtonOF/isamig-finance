from firebase_admin import firestore
from registration_validation import resolve_registration, normalize_cpf

@firestore.transactional
def apply_contacts(transaction, db, uid):
    claim_ref = db.collection("registration_claims").document(uid)
    decision_ref = db.collection("registration_decisions").document(uid)
    audit_ref = db.collection("registration_contact_audit").document(uid)
    account_ref = db.collection("users").document(uid)
    claim = claim_ref.get(transaction=transaction).to_dict() or {}
    decision = decision_ref.get(transaction=transaction).to_dict() or {}
    account = account_ref.get(transaction=transaction).to_dict() or {}
    if audit_ref.get(transaction=transaction).exists:
        return "already_applied"
    unit = decision.get("unit")
    if decision.get("decision") != "approved" or unit not in (
        "101","102","103","104","201","202","203","301","302","303","304",
        "401","402","403","404","501","502","503","504","601","602"
    ):
        return "not_approved"
    if account.get("status") != "approved" or account.get("unit") != unit:
        return "access_not_approved"
    resident_ref = db.collection("residents").document(unit)
    resident = resident_ref.get(transaction=transaction).to_dict() or {}
    cpf = normalize_cpf(claim.get("cpf"))
    if not cpf or normalize_cpf(resident.get("cpf")) != cpf:
        return "identity_changed"
    phone, email, whatsapp = claim.get("phone"), claim.get("email"), claim.get("whatsapp")
    if not isinstance(phone, str) or not phone.isascii() or not phone.isdigit() or not 10 <= len(phone) <= 13:
        return "invalid_contact"
    if not isinstance(email, str) or not email or email != account.get("email") or len(email) > 254 or type(whatsapp) is not bool:
        return "invalid_contact"
    contact_ref = db.collection("resident_contact_preferences").document(unit)
    previous = contact_ref.get(transaction=transaction).to_dict() or {}
    transaction.update(resident_ref, {"phone": phone, "email": email,
        "updatedBy": decision["decidedBy"], "updatedAt": firestore.SERVER_TIMESTAMP})
    transaction.set(contact_ref, {"whatsapp": whatsapp, "updatedAt": firestore.SERVER_TIMESTAMP})
    transaction.create(audit_ref, {"unit": unit, "before": {"phone": resident.get("phone"),
        "email": resident.get("email"), "whatsapp": previous.get("whatsapp")},
        "after": {"phone": phone, "email": email, "whatsapp": whatsapp},
        "approvedBy": decision["decidedBy"], "appliedAt": firestore.SERVER_TIMESTAMP})
    return "applied"
