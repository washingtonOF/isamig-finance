"""Read-only Cora mirror projection. Explicit historical scope required."""
import hashlib
from datetime import date
from finance_classification import classify_invoice

def payer_key(cpf):
    digits = "".join(c for c in str(cpf) if c in "0123456789")
    return hashlib.sha256(digits.encode()).hexdigest() if len(digits)==11 else None

RESIDENT_UNITS = frozenset(str(f*100+n) for f in range(1,7) for n in range(1,5 if f<6 else 3)) - {"204"}

def project(unit, uid, account, registry, link, all_links, invoices, month, today, confirmed_from, monetary_verified=False):
    if unit not in RESIDENT_UNITS or account.get("unit") != unit or account.get("status") != "approved" or account.get("role") != "resident":
        raise ValueError("Pilot account not eligible")
    if not uid or not account.get("email") or account["email"].strip().lower()!=str(registry.get("email","")).strip().lower():
        raise ValueError("Identity mismatch")
    payer=payer_key(registry.get("cpf"))
    if not payer or link.get("payer")!=payer or [u for u,v in all_links.items() if v.get("payer")==payer]!=[unit]:
        raise ValueError("Ambiguous payer")
    start=date.fromisoformat(confirmed_from)
    result=[]
    seen=set()
    for invoice in invoices:
        if invoice.get("payer")!=payer: continue
        due=date.fromisoformat(invoice["due_date"])
        if due<start or due.strftime("%Y-%m")!=month: continue
        identity=invoice["id"]
        if identity in seen: raise ValueError("Duplicate invoice")
        seen.add(identity)
        status=classify_invoice(invoice["status"],invoice["due_date"],today)
        if status=="unclassified": raise ValueError("Unknown status")
        amount=invoice.get("total_amount")
        result.append({"createdDate":str(invoice.get("created_at",""))[:10],"dueDate":due.isoformat(),"paidDate":str(invoice.get("paid_at") or "")[:10],"status":status,"amountCents":amount if monetary_verified and type(amount) is int and 0<=amount<=9007199254740991 else None})
    return {"paymentSchema":1,"authorizedUid":uid,"paymentEnabled":False,"invoices":result}
