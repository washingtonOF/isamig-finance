"""Pilot projection writer; requires explicit scope authorization before execution."""
from datetime import datetime
from zoneinfo import ZoneInfo
from google.cloud import firestore
from resident_invoice_projection import project

def sync(db, auth, confirmed_from, month):
    unit="102"
    accounts=list(db.collection("users").where("unit","==",unit).stream())
    approved=[s for s in accounts if s.to_dict().get("status")=="approved"]
    if len(approved)!=1: raise ValueError("Ambiguous account")
    uid=approved[0].id
    identity=auth.get_user(uid)
    if identity.disabled or not identity.email_verified: raise ValueError("Unverified account")
    today=datetime.now(ZoneInfo("America/Fortaleza")).date()
    @firestore.transactional
    def write(transaction):
        account=approved[0].reference.get(transaction=transaction).to_dict()
        if identity.email!=account.get("email"): raise ValueError("Auth mismatch")
        registry=db.collection("residents").document(unit).get(transaction=transaction).to_dict()
        links={s.id:s.to_dict() for s in db.collection("unit_payer_links").stream(transaction=transaction)}
        invoices=[s.to_dict() for s in db.collection("cora_invoice_private").where("payer","==",links[unit]["payer"]).stream(transaction=transaction)]
        payload=project(unit,uid,account,registry,links[unit],links,invoices,month,today,confirmed_from,True)
        payload["updatedAt"]=firestore.SERVER_TIMESTAMP
        transaction.set(db.collection("finance_units").document(unit).collection("months").document(month),payload)
    write(db.transaction())
