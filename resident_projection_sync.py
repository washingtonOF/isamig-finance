"""Pilot projection writer; requires explicit scope authorization before execution."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from google.cloud import firestore
from resident_invoice_projection import project, payer_key
from cora_client import CoraClient
from resident_payment_validation import valid_pix
from finance_classification import classify_invoice
import time

def sync(db, auth, confirmed_from, month):
    unit="102"
    accounts=list(db.collection("users").where("unit","==",unit).stream())
    approved=[s for s in accounts if s.to_dict().get("status")=="approved"]
    if len(approved)!=1: raise ValueError("Ambiguous account")
    uid=approved[0].id
    identity=auth.get_user(uid)
    if identity.disabled or not identity.email_verified: raise ValueError("Unverified account")
    today=datetime.now(ZoneInfo("America/Fortaleza")).date()
    link=db.collection("unit_payer_links").document(unit).get().to_dict() or {}
    payer=link.get("payer")
    registry=db.collection("residents").document(unit).get().to_dict() or {}
    if not payer or payer_key(registry.get("cpf"))!=payer or registry.get("email")!=identity.email:
        raise ValueError("Identity mismatch")
    client=CoraClient()
    details={}
    for snap in db.collection("cora_invoice_private").where("payer","==",payer).stream():
        row=snap.to_dict()
        if not str(row.get("due_date","")).startswith(month+"-"): continue
        time.sleep(5)
        detail=client.invoice_details(row["id"])
        document=(detail.get("customer") or {}).get("document") or {}
        if detail.get("id")!=row["id"] or payer_key(document.get("identity"))!=payer:
            raise ValueError("Detail identity mismatch")
        services=detail.get("services") or []
        description="; ".join(str(x.get("name",""))[:255] for x in services if isinstance(x,dict))[:500]
        pix=(detail.get("pix") or {}).get("emv")
        details[row["id"]]=(description,valid_pix(pix),detail.get("status"),detail.get("paid_at"),datetime.now(timezone.utc))
    print("Details checked:",len(details),"valid Pix:",sum(x[1] for x in details.values()))
    @firestore.transactional
    def write(transaction):
        account=approved[0].reference.get(transaction=transaction).to_dict()
        if identity.email!=account.get("email"): raise ValueError("Auth mismatch")
        registry=db.collection("residents").document(unit).get(transaction=transaction).to_dict()
        links={s.id:s.to_dict() for s in db.collection("unit_payer_links").stream(transaction=transaction)}
        invoices=[s.to_dict() for s in db.collection("cora_invoice_private").where("payer","==",links[unit]["payer"]).stream(transaction=transaction)]
        payload=project(unit,uid,account,registry,links[unit],links,invoices,month,today,confirmed_from,True)
        selected=[row for row in invoices if row.get("payer")==links[unit]["payer"] and str(row.get("due_date","")).startswith(month+"-") and row["due_date"]>=confirmed_from]
        if len(selected)!=len(payload["invoices"]): raise ValueError("Projection mismatch")
        for row, bill in zip(selected,payload["invoices"]):
            if row["id"] not in details: raise ValueError("Missing detail")
            description, pix_valid, status, paid_at, checked_at = details[row["id"]]
            bill["description"]=description
            if not isinstance(status,str): raise ValueError("Missing live status")
            category=classify_invoice(status,row["due_date"],today)
            if category=="unclassified":
                bill["status"]="processing" if status.upper() in ("PROCESSING","IN_PAYMENT") else "unknown"
            else:
                bill["status"]=category
            bill["paidDate"]=str(paid_at or "")[:10] if category=="paid" else ""
            bill["bankCheckedAt"]=checked_at.isoformat()
        # No payment tokens are published until a freshness policy is implemented.
        payload["updatedAt"]=firestore.SERVER_TIMESTAMP
        transaction.set(db.collection("finance_units").document(unit).collection("months").document(month),payload)
    write(db.transaction())
