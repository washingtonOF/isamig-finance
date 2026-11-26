import firebase_admin
from firebase_admin import firestore
from registration_validation import resolve_registration

def process(db):
    residents = {doc.id: doc.to_dict() for doc in db.collection("residents").stream()}
    for claim in db.collection("registration_claims").stream():
        data = claim.to_dict()
        if data.get("processedAt"):
            continue
        result = resolve_registration(data.get("cpf"), residents)
        # Keep identity and unit private until Master verifies the claimant.
        db.collection("registration_review_private").document(claim.id).set({
            "result": result,
            "processedAt": firestore.SERVER_TIMESTAMP,
        })
        claim.reference.update({
            "processedAt": firestore.SERVER_TIMESTAMP,
            "status": "awaiting_review" if result["status"] in ("matched", "review") else "not_accepted",
        })

if __name__ == "__main__":
    firebase_admin.initialize_app()
    process(firestore.client())
