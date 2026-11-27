"""Read-only Cora balance sync. Reject ambiguous monetary units."""
import os,json,re
from decimal import Decimal
from urllib.error import HTTPError
from google.oauth2 import service_account
from google.cloud import firestore
from cora_client import CoraClient

def parse_balance(data):
    value=data.get("balance") if isinstance(data,dict) else None
    # Only explicit decimal currency amounts; integer strings have ambiguous units.
    if not isinstance(value,str) or not re.fullmatch(r"-?[0-9]{1,13}\.[0-9]{2}",value):
        raise ValueError("Unverified balance format")
    cents=int(Decimal(value)*100)
    if abs(cents)>9007199254740991: raise ValueError("Balance out of range")
    return cents

def main():
    if os.environ.get("CORA_ENV")!="production": raise ValueError("Production required")
    info=json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"])
    if info.get("project_id")!="vinnas-del-mar-finance": raise ValueError("Wrong project")
    client=CoraClient()
    cents=parse_balance(client._json("/third-party/account/balance",token=client._access_token()))
    db=firestore.Client(project=info["project_id"],credentials=service_account.Credentials.from_service_account_info(info))
    db.collection("finance_admin").document("current_balance").set({"balanceSchema":1,"balanceCents":cents,"source":"cora","updatedAt":firestore.SERVER_TIMESTAMP})
    print("Balance synchronized successfully; values omitted.")
if __name__=="__main__":
    try: main()
    except Exception as e:
        print("Balance sync failed:",type(e).__name__,e.code if isinstance(e,HTTPError) else "")
        raise SystemExit(1) from None
