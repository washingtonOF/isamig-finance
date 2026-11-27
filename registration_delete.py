from firebase_admin import auth, firestore

def process_deletions(db):
    for req in db.collection("registration_delete_requests").stream():
        data = req.to_dict()
        if data.get("status") != "queued":
            continue
        uid = req.id
        try:
            user = auth.get_user(uid)
        except auth.UserNotFoundError:
            user = None
        account = db.collection("users").document(uid).get().to_dict() or {}
        decision = db.collection("registration_decisions").document(uid).get().to_dict() or {}
        email = (user.email if user else account.get("email")) or ""
        if email.lower() == "washington.s.souza@gmail.com" or (user and user.custom_claims) or account.get("status") not in (None, "pending") or decision.get("decision") == "approved" or (user and email != data.get("email")):
            req.reference.update({"status":"protected","finishedAt":firestore.SERVER_TIMESTAMP})
            continue
        if user:
            auth.update_user(uid, disabled=True)
            auth.revoke_refresh_tokens(uid)
        batch = db.batch()
        for name in ("users","registration_claims","registration_drafts","registration_review_private","registration_decisions","registration_auth_inventory"):
            batch.delete(db.collection(name).document(uid))
        batch.commit()
        if user:
            auth.delete_user(uid)
        req.reference.update({"status":"deleted","finishedAt":firestore.SERVER_TIMESTAMP})
