# IsaMig Finance
Protótipo local exclusivamente com dados fictícios. Não conecta ao banco. Não inserir dados reais nem expor à internet.

Execute `pip install -r requirements.txt` e `uvicorn main:app --host 127.0.0.1` e abra http://127.0.0.1:8000. Testes: `pytest -q`.

Próximas etapas: validar documentação Cora, implementar adaptador sandbox mTLS, autenticação, persistência e conciliação. Nunca armazenar credenciais no Git.
