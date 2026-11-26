from datetime import date
from finance_reports import report, reminder_preview
def test_paid_not_reminded():
    row={"unidade":"01","valor_centavos":25000,"status":"pago","vencimento":"2026-11-26"}
    assert reminder_preview([row],date(2026,11,26))==[]
    assert report([row])["total_centavos"]==25000
def test_due_preview():
    row={"unidade":"01","valor_centavos":25000,"status":"a_vencer","vencimento":"2026-11-26"}
    assert reminder_preview([row],date(2026,11,26))[0]["envio"] is False
