import unittest
from datetime import date
from resident_invoice_projection import project,payer_key

class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.payer=payer_key("12345678909")
        self.account={"unit":"102","status":"approved","role":"resident","email":"pilot@example.invalid"}
        self.registry={"cpf":"12345678909","email":"pilot@example.invalid"}
        self.link={"payer":self.payer}
        self.links={"102":self.link}
        self.rows=[{"id":"a","payer":self.payer,"due_date":"2026-11-01","status":"OPEN","total_amount":25000},{"id":"b","payer":"other","due_date":"2026-11-01","status":"PAID"},{"id":"c","payer":self.payer,"due_date":"2026-10-01","status":"PAID"}]
    def run_projection(self):
        return project("102","pilot",self.account,self.registry,self.link,self.links,self.rows,"2026-11",date(2026,11,27),"2026-11-01")
    def test_isolation(self):
        result=self.run_projection()
        self.assertEqual(len(result["invoices"]),1)
        self.assertEqual(result["invoices"][0]["status"],"overdue")
        self.assertIsNone(result["invoices"][0]["amountCents"])
        self.assertFalse(result["paymentEnabled"])
    def test_ambiguous(self):
        self.links["103"]=self.link
        with self.assertRaises(ValueError): self.run_projection()
    def test_revoked(self):
        self.account["status"]="revoked"
        with self.assertRaises(ValueError): self.run_projection()
    def test_email_mismatch(self):
        self.registry["email"]="other@example.invalid"
        with self.assertRaises(ValueError): self.run_projection()
    def test_duplicate(self):
        self.rows.append(self.rows[0])
        with self.assertRaises(ValueError): self.run_projection()
    def test_scope(self):
        self.rows[0]["due_date"]="2026-10-31"
        self.assertEqual(self.run_projection()["invoices"],[])
