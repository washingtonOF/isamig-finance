import csv
from io import StringIO
from fastapi import APIRouter
from fastapi.responses import Response
from finance_reports import report, reminder_preview
def build_router(source):
    router=APIRouter(prefix="/api/analytics")
    @router.get("/relatorio")
    def summary():
        return {"simulado":True,**report(source())}
    @router.get("/boletos.csv")
    def export():
        out=StringIO()
        writer=csv.DictWriter(out,fieldnames=["unidade","valor_centavos","status","vencimento"])
        writer.writeheader(); writer.writerows(source())
        return Response(out.getvalue(),media_type="text/csv; charset=utf-8")
    @router.get("/cobrancas/preview")
    def preview():
        return {"simulado":True,"envio_habilitado":False,"eventos":reminder_preview(source())}
    return router
