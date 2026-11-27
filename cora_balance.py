"""Read-only Cora balance sync. Reject ambiguous monetary units."""
import os,json,re
from decimal import Decimal
from urllib.error import HTTPError
from google.oauth2 import service_account
from google.cloud import firestore
from cora_client import CoraClient

def parse_balance(data):
    value=data.get("balance") if isinstance(data,dict) else None
    if type(value) is not int or abs(value)>9007199254740991:
        raise ValueError("Unverified balance format")
    return value

def main():
    if os.environ.get("CORA_ENV")!="production": raise ValueError("Production required")
    info=json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"])
    if info.get("project_id")!="vinnas-del-mar-finance": raise ValueError("Wrong project")
    print("Project validated; initializing mTLS",flush=True)
    client=CoraClient()
    print("Requesting bank balance",flush=True)
    data=client._json("/third-party/account/balance",token=client._access_token())
    value=data.get("balance") if isinstance(data,dict) else None
    shape=("integer_string" if isinstance(value,str) and re.fullmatch(r"-?[0-9]+",value) else "decimal_string" if isinstance(value,str) and re.fullmatch(r"-?[0-9]+[.,][0-9]+",value) else "other_string" if isinstance(value,str) else type(value).__name__)
    print("Balance response: object="+str(isinstance(data,dict))+"; field format="+shape,flush=True)
    cents=parse_balance(data)
    # Statement ending balance is explicitly documented in cents.
    from datetime import datetime,timedelta
    from zoneinfo import ZoneInfo
    today=datetime.now(ZoneInfo("America/Fortaleza")).date()
    statement=client.statement((today-timedelta(days=31)).isoformat(),today.isoformat())
    end=statement.get("end") if isinstance(statement,dict) else None
    reference=end.get("balance") if isinstance(end,dict) else None
    if type(reference) is not int or reference!=cents:
        print("Balance unit cross-check not confirmed; no publication.",flush=True)
        raise ValueError("Balance reconciliation required")
    print("Balance verified against statement ending balance in cents",flush=True)
    db=firestore.Client(project=info["project_id"],credentials=service_account.Credentials.from_service_account_info(info))
    observed=datetime.now(ZoneInfo("America/Fortaleza"))
    payload={"balanceSchema":1,"balanceCents":cents,"source":"cora","updatedAt":firestore.SERVER_TIMESTAMP}
    batch=db.batch()
    batch.set(db.collection("finance_admin").document("current_balance"),payload)
    batch.set(db.collection("finance_admin").document("balance_day_"+observed.date().isoformat()),payload)
    batch.commit()
    print("Balance synchronized successfully; values omitted.")
if __name__=="__main__":
    try: main()
    except Exception as e:
        print("Balance sync failed:",type(e).__name__,e.code if isinstance(e,HTTPError) else "")
        raise SystemExit(1) from None
