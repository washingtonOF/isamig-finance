"""Private server-side Cora read-only transport. Not exposed as an HTTP route."""
import json
import ssl
from urllib.request import Request, build_opener, HTTPSHandler, HTTPRedirectHandler
from urllib.parse import urlencode, quote
from datetime import date
import os
import time

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

class CoraClient:
    def __init__(self):
        environment = os.environ.get("CORA_ENV", "stage")
        if environment not in ("stage", "production"):
            raise ValueError("Invalid Cora environment")
        self.base = ("https://matls-clients.api.stage.cora.com.br"
                     if environment == "stage" else "https://matls-clients.api.cora.com.br")
        self.client_id = os.environ["CORA_CLIENT_ID"]
        context = ssl.create_default_context()
        context.load_cert_chain(os.environ["CORA_CERT_PATH"], os.environ["CORA_KEY_PATH"])
        self.opener = build_opener(HTTPSHandler(context=context), NoRedirect())
        self._token = None
        self._expiry = 0

    def _json(self, path, data=None, token=None):
        headers = {"Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        if token:
            headers["Authorization"] = "Bearer " + token
        with self.opener.open(Request(self.base + path, data=data, headers=headers), timeout=30) as response:
            return json.load(response)

    def _access_token(self):
        if self._token is None or time.monotonic() >= self._expiry:
            result = self._json("/token", urlencode({"grant_type": "client_credentials", "client_id": self.client_id}).encode())
            self._token = result["access_token"]
            self._expiry = time.monotonic() + max(0, int(result["expires_in"]) - 60)
        return self._token

    def _period(self, start, end, page):
        if date.fromisoformat(start) > date.fromisoformat(end) or type(page) is not int or page < 1:
            raise ValueError("Invalid period or page")
        return urlencode({"start": start, "end": end, "page": page})

    def invoices(self, start, end, page=1):
        return self._json("/v2/invoices/?" + self._period(start, end, page), token=self._access_token())

    def statement(self, start, end, page=1):
        return self._json("/bank-statement/statement?" + self._period(start, end, page), token=self._access_token())

    def invoice_details(self, invoice_id):
        if not isinstance(invoice_id, str) or not invoice_id or invoice_id in (".", ".."):
            raise ValueError("Invalid invoice ID")
        return self._json("/v2/invoices/" + quote(invoice_id, safe=""), token=self._access_token())
