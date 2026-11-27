from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from finance_pagination import collect_pages
from google.cloud import firestore

def sync_month(db, client, start, end, invoices, payers, links):
    boundaries=[]
    def capture(start,end,page=1):
        response=client.statement(start,end,page=page)
        def balance(key):
            obj=response.get(key) if isinstance(response,dict) else None
            value=obj.get("balance") if isinstance(obj,dict) else None
            return value if type(value) is int and abs(value)<=9007199254740991 else None
        boundaries.append((balance("start"),balance("end")))
        return response
    entries=collect_pages(capture,start,end,"entries",50)
    rows=[]
    totals={"credit":0,"debit":0}
    for row in entries:
        kind=row["type"].lower()
        amount=row["amount"]
        if kind not in totals or type(amount) is not int or not 0<=amount<=9007199254740991:
            raise ValueError("Unknown movement")
        stamp=datetime.fromisoformat(row["createdAt"].replace("Z","+00:00"))
        if stamp.tzinfo is None: raise ValueError("Missing timezone")
        day=stamp.astimezone(ZoneInfo("America/Fortaleza")).date().isoformat()
        if not start<=day<=end: raise ValueError("Outside period")
        description=row["transaction"]["description"]
        if not isinstance(description,str): raise ValueError("Invalid description")
        totals[kind]+=amount
        rows.append({"date":day,"transactionType":str(row["transaction"].get("type",""))[:100],"description":description[:500],"type":kind,"amountCents":amount})
    matched=0
    for raw, row in zip(entries,rows):
        if row["type"]!="credit" or row["transactionType"].upper()!="PAYMENT": continue
        invoice=invoices.get(raw["transaction"].get("id"))
        if not invoice or invoice.get("status","").upper()!="PAID" or invoice.get("total_paid")!=row["amountCents"]: continue
        paid=str(invoice.get("paid_at") or "")[:10]
        if paid!=row["date"]: continue
        payer=invoice.get("payer")
        if not payer: continue
        row["payerName"]=payers.get(payer,"")
        row["invoiceMatched"]=True
        row["candidateUnits"]=sorted(links.get(payer,[]))
        matched+=1
    print("Exact invoice matches:",matched,"of",len(rows))
    if len(rows)>700: raise ValueError("Document size guard")
    payload={"statementSchema":2,"statementCoverageStart":start,"statementCoverageEnd":end,"statementEntries":rows,"statementTotalsCents":totals,"statementUpdatedAt":firestore.SERVER_TIMESTAMP}
    initial,final=boundaries[0]
    consistent=initial is not None and final is not None and all(pair==(initial,final) for pair in boundaries)
    calculated=initial+totals["credit"]-totals["debit"] if consistent else None
    safe=consistent and all(abs(v)<=9007199254740991 for v in (totals["credit"],totals["debit"],calculated,calculated-final))
    payload["reconciliation"]={"schema":1,"status":("matched" if calculated==final else "difference") if safe else "unavailable","openingCents":initial if safe else None,"closingCents":final if safe else None,"calculatedCents":calculated if safe else None,"differenceCents":calculated-final if safe else None,"coverageStart":start,"coverageEnd":end}
    db.collection("finance_admin").document(start[:7]).set(payload,merge=True)
    print("Statement mirror published:",len(rows))

def sync_statement(db, client, months=12):
    today=datetime.now(ZoneInfo("America/Fortaleza")).date()
    invoices={d.get("id"):d for snap in db.collection("cora_invoice_private").stream() if (d:=snap.to_dict()).get("id")}
    payers={snap.id:(snap.to_dict().get("name") or "") for snap in db.collection("cora_import_private").stream()}
    links={}
    for snap in db.collection("unit_payer_links").stream():
        d=snap.to_dict()
        payer=d.get("payer") or d.get("payerKey") or d.get("payerId")
        if payer: links.setdefault(payer,[]).append(snap.id)
    month=today.replace(day=1)
    for i in range(months):
        next_month=(month.replace(day=28)+timedelta(days=4)).replace(day=1)
        end=min(today,next_month-timedelta(days=1))
        sync_month(db,client,month.isoformat(),end.isoformat(),invoices,payers,links)
        month=(month-timedelta(days=1)).replace(day=1)
