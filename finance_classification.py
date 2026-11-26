"""Conservative invoice classification; unknown states must not become debt."""
from datetime import date

def classify_invoice(status, due_date, today):
    if not isinstance(status, str) or not isinstance(today, date):
        raise ValueError("Invalid invoice")
    status = status.strip().upper()
    if status == "PAID":
        return "paid"
    if status in ("CANCELED", "CANCELLED"):
        return "cancelled"
    if status in ("OPEN", "PENDING", "LATE", "OVERDUE"):
        due = date.fromisoformat(due_date)
        return "overdue" if due < today else "pending"
    return "unclassified"

def summarize_invoices(rows, today):
    counts = dict(paid=0, cancelled=0, overdue=0, pending=0, unclassified=0)
    for row in rows:
        counts[classify_invoice(row.get("status"), row.get("due_date"), today)] += 1
    return counts
