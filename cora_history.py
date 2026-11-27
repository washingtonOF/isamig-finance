import os,json,hashlib,time,calendar
from datetime import date,datetime
from zoneinfo import ZoneInfo
from urllib.error import HTTPError
from google.oauth2 import service_account
from google.cloud import firestore
from google.api_core.exceptions import AlreadyExists
from cora_client import CoraClient
from finance_pagination import collect_pages

def main():
    info=json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"])
    if info.get("project_id")!="vinnas-del-mar-finance": raise ValueError("Wrong project")
    db=firestore.Client(project=info["project_id"],credentials=service_account.Credentials.from_service_account_info(info))
    client=CoraClient()
    today=datetime.now(ZoneInfo("America/Fortaleza")).date()
    def retry(fn,*args,**kwargs):
        for attempt in range(5):
            try:
                time.sleep(5)
                return fn(*args,**kwargs)
            except HTTPError as e:
                if e.code not in (429,500,502,503,504) or attempt==4: raise
                header=e.headers.get("Retry-After","") if e.headers else ""
                delay=int(header) if header.isdigit() else 60
                if delay>300: raise
                time.sleep(max(5,delay))
    year,month=today.year,today.month
    while year>=2019:
        start=date(year,month,1)
        end=min(today,date(year,month,calendar.monthrange(year,month)[1]))
        period=start.strftime("%Y-%m")
        checkpoint=db.collection("cora_history_progress").document(period)
        if not checkpoint.get().exists or month==today.month and year==today.year:
            rows=collect_pages(lambda *args,**kwargs:retry(client.invoices,*args,**kwargs),start.isoformat(),end.isoformat(),"items",20)
            created=0
            for row in rows:
                key=hashlib.sha256(row["id"].encode()).hexdigest()
                ref=db.collection("cora_invoice_private").document(key)
                previous=ref.get().to_dict() or {}
                payer=previous.get("payer")
                if not payer:
                    detail=retry(client.invoice_details,row["id"])
                    customer=detail.get("customer") or {}
                    document=customer.get("document") or {}
                    identity=document.get("identity","") if isinstance(document,dict) else ""
                    digits="".join(ch for ch in str(identity) if ch in "0123456789")
                    name=customer.get("name")
                    if len(digits) in (11,14) and isinstance(name,str) and name.strip():
                        payer=hashlib.sha256(digits.encode()).hexdigest()
                        try:
                            db.collection("cora_import_private").document(payer).create({"name":name.strip(),"document":digits,"email":customer.get("email") if isinstance(customer.get("email"),str) else "","phone":customer.get("telephone") if isinstance(customer.get("telephone"),str) else "","suggestedUnit":None,"source":"cora","status":"pending_review","importedAt":firestore.SERVER_TIMESTAMP})
                            created+=1
                        except AlreadyExists: pass
                payload={k:row[k] for k in ("id","status","created_at","due_date","paid_at","total_amount") if k in row}
                payload.update(payer=payer,updatedAt=firestore.SERVER_TIMESTAMP)
                ref.set(payload,merge=True)
            from finance_classification import summarize_invoices
            counts = summarize_invoices(rows, today)
            if counts["unclassified"]:
                raise ValueError("Unclassified invoice status")
            db.collection("finance_admin").document(period).set({
                "period":period,"coverageStart":start.isoformat(),"coverageEnd":end.isoformat(),
                "invoiceCounts":dict(counts,total=len(rows)),
                "updatedAt":firestore.SERVER_TIMESTAMP,"scope":"invoice_query_period",
                "monetaryDataAvailable":False
            },merge=True)
            checkpoint.set({"count":len(rows),"completedAt":firestore.SERVER_TIMESTAMP,"start":start.isoformat(),"end":end.isoformat()})
            print(period,"boletos",len(rows),"novos pagadores",created,flush=True)
        month-=1
        if month==0: year-=1;month=12
if __name__=="__main__":
    try: main()
    except Exception as e:
        print("Importacao interrompida:",type(e).__name__,getattr(e,"code","") if isinstance(e,HTTPError) else "",flush=True)
        raise SystemExit(1) from None
