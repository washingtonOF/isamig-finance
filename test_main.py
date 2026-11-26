from fastapi.testclient import TestClient
from main import app
client=TestClient(app)
def test_resumo():
    r=client.get("/api/resumo").json()
    assert r["simulado"] and r["total_centavos"]==r["pago"]+r["vencido"]+r["a_vencer"]
def test_boletos():
    assert len(client.get("/api/boletos").json()["boletos"])==22
def test_exports():
    assert client.get("/relatorios/pdf").content.startswith(b"%PDF")
    assert client.get("/relatorios/excel").content.startswith(b"PK")
