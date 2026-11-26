import firebase_admin
from firebase_admin import firestore
from registration_validation import resolve_registration
from registration_contacts import apply_contacts

def process(db):
    residents = {doc.id: doc.to_dict() for doc in db.collection("residents").stream()}
    for claim in db.collection("registration_claims").stream():
        data = claim.to_dict()
        if data.get("processedAt"):
            continue
        result = resolve_registration(data.get("cpf"), residents)
        batch = db.batch()
        batch.set(db.collection("registration_review_private").document(claim.id), {
            "result": result,
            "processedAt": firestore.SERVER_TIMESTAMP,
        })
        # Identical public-facing status for every result; no CPF lookup oracle.
        batch.update(claim.reference, {
            "processedAt": firestore.SERVER_TIMESTAMP,
            "status": "awaiting_review",
        })
        batch.commit()

def process_approved_contacts(db):
    for decision in db.collection("registration_decisions").where("decision", "==", "approved").stream():
        apply_contacts(db.transaction(), db, decision.id)

if __name__ == "__main__":
    firebase_admin.initialize_app()
    db = firestore.client()
    process(db)
    process_approved_contacts(db)
