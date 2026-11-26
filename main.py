from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from datetime import date, timedelta
from io import BytesIO
from openpyxl import Workbook
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
app = FastAPI(title="IsaMig Finance", version="0.1.0")
def boletos():
    return [{"unidade":f"{i:02}", "valor_centavos":25000,"status":"pago" if i<=11 else "vencido" if i<=16 else "a_vencer","vencimento":str(date.today()+timedelta(days=-5 if i<=16 else 5))} for i in range(1,23)]
@app.get("/api/boletos")
def listar():
    return {"simulado":True,"boletos":boletos()}
@app.get("/api/resumo")
def resumo():
    rows=boletos()
    totals={s:sum(r["valor_centavos"] for r in rows if r["status"]==s) for s in ("pago","vencido","a_vencer")}
    return {"simulado":True,"total_centavos":sum(totals.values()),**totals,"inadimplencia_percentual":round(100*sum(r["status"]=="vencido" for r in rows)/len(rows),2)}
@app.get("/relatorios/excel")
def excel():
    wb=Workbook()
    ws=wb.active
    ws.title="Dados ficticios"
    ws.append(["Unidade","Valor (R$)","Status","Vencimento"])
    for r in boletos():
        ws.append([r["unidade"],r["valor_centavos"]/100,r["status"],r["vencimento"]])
    out=BytesIO()
    wb.save(out)
    out.seek(0)
    return StreamingResponse(out,media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",headers={"Content-Disposition":"attachment; filename=simulacao.xlsx"})
@app.get("/relatorios/pdf")
def pdf():
    out=BytesIO()
    rows=[["Unidade","Valor (R$)","Status","Vencimento"]]+[[r["unidade"],str(r["valor_centavos"]/100),r["status"],r["vencimento"]] for r in boletos()]
    SimpleDocTemplate(out).build([Paragraph("IsaMig Finance - Dados ficticios",getSampleStyleSheet()["Title"]),Table(rows,repeatRows=1)])
    out.seek(0)
    return StreamingResponse(out,media_type="application/pdf",headers={"Content-Disposition":"attachment; filename=simulacao.pdf"})
@app.get("/",response_class=HTMLResponse)
def home():
    return """<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>IsaMig Finance</title><style>body{font:16px system-ui;background:#eef2f7;color:#14243b;padding:24px}main{max-width:1000px;margin:auto}section{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px}article,table{background:white;padding:20px;border-radius:12px}strong{display:block;font-size:26px}td,th{padding:10px;text-align:left}table{width:100%}</style><main><h1>IsaMig Finance</h1><p>Ambiente demonstrativo — dados fictícios</p><section id="cards"></section><p><a href="/relatorios/pdf">PDF</a> · <a href="/relatorios/excel">Excel</a> · <a href="/docs">API</a></p><table><thead><tr><th>Unidade</th><th>Valor</th><th>Status</th><th>Vencimento</th></tr></thead><tbody id="rows"></tbody></table></main><script>const money=n=>(n/100).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});async function load(){const s=await fetch('/api/resumo').then(r=>r.json());for(const [k,v] of Object.entries({Total:s.total_centavos,Pago:s.pago,Vencido:s.vencido,'A vencer':s.a_vencer})){const a=document.createElement('article');a.textContent=k;const b=document.createElement('strong');b.textContent=money(v);a.append(b);document.getElementById('cards').append(a)}const d=await fetch('/api/boletos').then(r=>r.json());for(const b of d.boletos){const tr=document.getElementById('rows').insertRow();for(const v of [b.unidade,money(b.valor_centavos),b.status,b.vencimento])tr.insertCell().textContent=v}}load().catch(()=>document.querySelector('main').append('Falha ao carregar dados.'))</script></html>"""
