import unittest
from datetime import date
from finance_classification import classify_invoice, summarize_invoices

class ClassificationTests(unittest.TestCase):
    def test_due_today(self):
        self.assertEqual(classify_invoice("OPEN","2026-11-26",date(2026,11,26)),"pending")
    def test_overdue(self):
        self.assertEqual(classify_invoice("OPEN","2026-11-25",date(2026,11,26)),"overdue")
    def test_paid(self):
        self.assertEqual(classify_invoice("PAID",None,date(2026,11,26)),"paid")
    def test_cancelled(self):
        self.assertEqual(classify_invoice("CANCELLED",None,date(2026,11,26)),"cancelled")
    def test_unknown(self):
        self.assertEqual(classify_invoice("OTHER",None,date(2026,11,26)),"unclassified")
    def test_invalid_date(self):
        with self.assertRaises(ValueError):
            classify_invoice("OPEN","invalid",date(2026,11,26))
