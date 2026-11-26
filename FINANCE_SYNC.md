# Sincronização financeira — contrato de publicação

- Cora: somente GET para recursos financeiros; POST exclusivamente para token OAuth.
- Firebase: projeto vinnas-del-mar-finance, identidade de serviço dedicada.
- finance_admin/{YYYY-MM}: projeção administrativa validada.
- finance_public/{YYYY-MM}: somente totais consolidados, sem nomes, CPF, identificadores bancários ou descrições livres.
- finance_units/{unit}/months/{YYYY-MM}: somente boletos com vínculo cadastral confirmado; nunca inferir autorização apenas pelo nome do pagador.
- Não publicar resposta bancária bruta, tokens ou dados pessoais em logs, artefatos ou Git.
- Não substituir dados existentes por resultados parciais, paginação incompleta ou falhas.
- Validar moeda, unidade monetária, datas, status, paginação e identificadores antes de gravar.
- Registrar data da última sincronização bem-sucedida; distinguir saldo indisponível de zero.
- Ativar agendamento somente após validação da primeira importação e das regras de acesso.
- Publicar firestore.rules no console e testar perfis Master, administrativo, condômino e usuário revogado.
- Preferir identidade federada sem chave persistente; enquanto não disponível, usar secret rotacionado e permissões IAM mínimas.
