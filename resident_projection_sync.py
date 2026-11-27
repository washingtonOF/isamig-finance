"""Pilot projection writer; requires explicit scope authorization before execution."""
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from google.cloud import firestore
from resident_invoice_projection import project, payer_key, RESIDENT_UNITS
from cora_client import CoraClient
from resident_payment_validation import valid_pix
from finance_classification import classify_invoice
import time

def sync(db, auth, confirmed_from, month, unit="102"):
    if unit not in RESIDENT_UNITS: raise ValueError("Invalid resident unit")
    accounts=list(db.collection("users").where("unit","==",unit).stream())
    approved=[s for s in accounts if s.to_dict().get("status")=="approved"]
    if unit=="204":
        identity=auth.get_user_by_email("washington.s.souza@gmail.com")
        if not any(p.provider_id=="google.com" for p in identity.provider_data): raise ValueError("Master provider mismatch")
        uid=identity.uid
        def read_account(transaction=None):
            return {"unit":"204","role":"master","status":"approved","email":identity.email}
    else:
        if len(approved)!=1: raise ValueError("Ambiguous account")
        uid=approved[0].id
        identity=auth.get_user(uid)
        def read_account(transaction=None):
            return approved[0].reference.get(transaction=transaction).to_dict()
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
        slip=((detail.get("payment_options") or {}).get("bank_slip") or {})
        url=slip.get("url")
        
        from urllib.parse import urlsplit
        parsed=urlsplit(url) if isinstance(url,str) else None
        
        safe_url=url if parsed and parsed.scheme=="https" and parsed.hostname and (parsed.hostname in ("cora.com.br","storage.googleapis.com") or parsed.hostname.endswith(".cora.com.br")) and not parsed.username and not parsed.password and parsed.port in (None,443) else None
        details[row["id"]]=(description,valid_pix(pix),detail.get("status"),detail.get("paid_at"),datetime.now(timezone.utc),pix,safe_url)
    print("Details checked:",len(details),"valid Pix:",sum(x[1] for x in details.values()))
    @firestore.transactional
    def write(transaction):
        account=read_account(transaction)
        if identity.email!=account.get("email"): raise ValueError("Auth mismatch")
        registry=db.collection("residents").document(unit).get(transaction=transaction).to_dict()
        links={s.id:s.to_dict() for s in db.collection("unit_payer_links").stream(transaction=transaction)}
        invoices=[s.to_dict() for s in db.collection("cora_invoice_private").where("payer","==",links[unit]["payer"]).stream(transaction=transaction)]
        payload=project(unit,uid,account,registry,links[unit],links,invoices,month,today,confirmed_from,True)
        selected=[row for row in invoices if row.get("payer")==links[unit]["payer"] and str(row.get("due_date","")).startswith(month+"-") and row["due_date"]>=confirmed_from]
        if len(selected)!=len(payload["invoices"]): raise ValueError("Projection mismatch")
        verified_bills=[]
        for row, bill in zip(selected,payload["invoices"]):
            if row["id"] not in details: raise ValueError("Missing detail")
            description, pix_valid, status, paid_at, checked_at, pix, slip_url = details[row["id"]]
            import re
            units_named=set(re.findall(r"\b(?:unidade|apartamento|ap)\s*[:#-]?\s*(\d{3})\b",description,re.I))
            if units_named!={unit}: continue
            verified_bills.append(bill)
            bill["description"]=description
            if not isinstance(status,str): raise ValueError("Missing live status")
            category=classify_invoice(status,row["due_date"],today)
            if category=="unclassified":
                bill["status"]="processing" if status.upper() in ("PROCESSING","IN_PAYMENT") else "unknown"
            else:
                bill["status"]=category
            bill["paidDate"]=str(paid_at or "")[:10] if category=="paid" else ""
            bill["bankCheckedAt"]=checked_at.isoformat()
            if slip_url and status.upper() in ("OPEN","LATE","OVERDUE") and category in ("pending","overdue"):
                bill["boletoUrl"]=slip_url
                bill["boletoExpiresAt"]=(checked_at+timedelta(minutes=30)).isoformat()
            if pix_valid and status.upper() in ("OPEN","LATE","OVERDUE") and category in ("pending","overdue"):
                bill["pixCode"]=pix
                bill["pixExpiresAt"]=(checked_at+timedelta(minutes=30)).isoformat()
        payload["invoices"]=verified_bills
        payload["paymentEnabled"]=any("pixCode" in bill for bill in payload["invoices"])
        payload["updatedAt"]=firestore.SERVER_TIMESTAMP
        transaction.set(db.collection("finance_units").document(unit).collection("months").document(month),payload)
    write(db.transaction())

def sync_authorized_residents(db, auth, month):
    """Owner-authorized rollout, retaining identity and unique payer checks."""
    blocked=0
    for unit in sorted(RESIDENT_UNITS - {"401","501"}):
        try:
            if unit=="204":
                uid=auth.get_user_by_email("washington.s.souza@gmail.com").uid
            else:
                accounts=[s for s in db.collection("users").where("unit","==",unit).stream() if s.to_dict().get("status")=="approved"]
                if len(accounts)!=1:
                    print("Projection skipped:",unit,"account unavailable or ambiguous")
                    continue
                account=accounts[0].to_dict()
                if account.get("role") not in ("resident","administrative"): continue
                uid=accounts[0].id
            scope=db.collection("resident_projection_scopes").document(unit).get().to_dict() or {}
            start=max("2025-12-01",scope.get("confirmedFrom") or "2025-12-01")
            if scope.get("enabled") is False or (scope.get("authorizedUid") and scope["authorizedUid"]!=uid):
                print("Projection skipped:",unit,"scope restricted")
                continue
            y,m=map(int,month.split("-"))
            periods=[f"{(y*12+m-1-i)//12:04d}-{(y*12+m-1-i)%12+1:02d}" for i in range(12)]
            for period in periods:
                if period>=start[:7]: sync(db,auth,start,period,unit)
            print("Projection refreshed:",unit)
        except Exception as exc:
            blocked+=1
            print("Projection blocked:",unit,type(exc).__name__)
    print("Units blocked:",blocked)
