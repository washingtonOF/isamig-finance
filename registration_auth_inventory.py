from firebase_admin import auth, firestore

def sync_auth_inventory(db):
    collection = db.collection("registration_auth_inventory")
    seen = set()
    for user in auth.list_users().iterate_all():
        if not user.email or user.email.lower() == "washington.s.souza@gmail.com":
            continue
        seen.add(user.uid)
        collection.document(user.uid).set({
            "email": user.email,
            "emailVerified": bool(user.email_verified),
            "disabled": bool(user.disabled),
            "createdMillis": user.user_metadata.creation_timestamp,
            "updatedAt": firestore.SERVER_TIMESTAMP,
        })
    for record in collection.stream():
        if record.id not in seen:
            record.reference.delete()
