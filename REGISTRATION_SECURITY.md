# Cadastro seguro — Vinnas Del Mar

## Fluxo de produção

No plano Spark, não disponibilizar consulta pública por CPF. A interface coleta o CPF, mas não revela existência, nome ou unidade antes da verificação de identidade. A conta de autenticação com email verificado pode enviar uma solicitação privada. O processador associa o CPF ao cadastro oficial internamente. O Master verifica a identidade por canal independente antes de autorizar o acesso ou aplicar alterações cadastrais. A confirmação de email novo não comprova titularidade do CPF.

## Restrições

- Uma solicitação por UID; não retornar resultado de existência de CPF ao solicitante.
- Não autorizar acesso por correspondência de CPF isolada.
- AP 204 reservado ao Master; casos ambíguos exigem revisão.
- Telefone, WhatsApp e email propostos ficam separados do cadastro oficial até aprovação.
- Não modificar Cora; não sobrescrever alterações locais.
- Não publicar regras ou formulário até testes de autorização e integração.

## Pendências

Implementar interface autenticada, revisão privada, proteção contra abuso, aprovação transacional, auditoria e testes de regras. Para confirmação imediata de nome/unidade antes de criar conta, será necessário mecanismo adicional de identidade, como convite individual de alta entropia emitido pelo Master, ou serviço confiável de verificação. Não expor índices de CPF ao navegador.
