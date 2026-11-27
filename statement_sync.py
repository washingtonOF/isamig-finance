from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from finance_pagination import collect_pages
from google.cloud import firestore

def sync_month(db, client, start, end):
    entries=collect_pages(client.statement,start,end,"entries",50)
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
    if len(rows)>700: raise ValueError("Document size guard")
    payload={"statementSchema":2,"statementCoverageStart":start,"statementCoverageEnd":end,"statementEntries":rows,"statementTotalsCents":totals,"statementUpdatedAt":firestore.SERVER_TIMESTAMP}
    db.collection("finance_admin").document(start[:7]).set(payload,merge=True)
    print("Statement mirror published:",len(rows))

def sync_statement(db, client):
    today=datetime.now(ZoneInfo("America/Fortaleza")).date()
    month=today.replace(day=1)
    for i in range(12):
        next_month=(month.replace(day=28)+timedelta(days=4)).replace(day=1)
        end=min(today,next_month-timedelta(days=1))
        sync_month(db,client,month.isoformat(),end.isoformat())
        month=(month-timedelta(days=1)).replace(day=1)
