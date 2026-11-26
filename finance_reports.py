from collections import defaultdict
from datetime import date
def report(rows):
    by_status=defaultdict(lambda: {"quantidade":0,"valor_centavos":0})
    by_unit=defaultdict(lambda: {"quantidade":0,"valor_centavos":0,"vencido_centavos":0})
    for r in rows:
        s=by_status[r["status"]]; s["quantidade"]+=1; s["valor_centavos"]+=r["valor_centavos"]
        u=by_unit[r["unidade"]]; u["quantidade"]+=1; u["valor_centavos"]+=r["valor_centavos"]
        if r["status"]=="vencido": u["vencido_centavos"]+=r["valor_centavos"]
    return {"status":dict(by_status),"unidades":dict(by_unit),"total_centavos":sum(r["valor_centavos"] for r in rows)}
def reminder_preview(rows, today=None):
    today=today or date.today()
    rules={-5:"lembrete antecipado",0:"vencimento",3:"pendencia",10:"regularizacao"}
    result=[]
    for r in rows:
        if r["status"] not in ("a_vencer","vencido"): continue
        delta=(today-date.fromisoformat(r["vencimento"])).days
        if delta in rules:
            result.append({"unidade":r["unidade"],"evento":rules[delta],"dias":delta,"valor_centavos":r["valor_centavos"],"vencimento":r["vencimento"],"envio":False})
    return result
