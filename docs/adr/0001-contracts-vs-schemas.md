# ADR 0001: o que fazer com `api/contracts` e `app/schemas`

Status: proposto
Data: 2026-08-16
Ref: REFACTOR_PLAN.md, itens R5 e R12

O R12 pedia um spike com recomendação escrita, não um diff. Este é o
documento. O R5, a auditoria, foi feito junto e está descrito abaixo.

## O problema

Duas bibliotecas descrevem a mesma API.

`app/api/contracts/` (900 LoC, 62 `api.model`) alimenta o Swagger do
flask-restx. `app/schemas/` (1.200 LoC) valida e serializa com marshmallow.

Os dois lados são mantidos à mão e não têm nada que os force a concordar.

## O que a auditoria encontrou

22 modelos de request nos contracts, 24 schemas de request. Todos os 22
casaram com um schema por nome.

Três campos documentados que o serviço descarta em silêncio, porque o
`BaseSchema` usa `unknown = EXCLUDE`:

| Campo | Modelo | Por quê é fantasma |
|---|---|---|
| `ano` | `OnibusCreateRequest` | Nunca existiu no modelo `Onibus`, no schema nem no `create_onibus` |
| `pontos`, `horarios` | `RotaUpdateRequest` | `update_rota` trata só nome e os dois ids padrão. Os dois têm endpoint próprio |
| `salario` | `MotoristaCreateRequest` | A coluna saiu de `Gestor` na migração `a1b2c3d4e5f6` e `Motorista` nunca a teve |

Os três foram corrigidos no PR que traz este documento.

**A deriva é menor do que o plano supunha.** O item R5 nasceu apontando o
`viagem_contract`, que anunciava `horario_id`, `motorista_id` e `veiculo_id`.
Aquele caso já tinha sido corrigido pela PR #30, e ninguém atualizou o plano.
Sobravam três campos em 62 modelos.

## Recomendação: manter os dois, e travar a deriva com teste

Não unificar. Os três motivos, em ordem de peso.

**1. O custo de unificar não se paga.** A deriva medida é de 3 campos.
Gerar Swagger a partir do marshmallow exigiria `apispec` ou equivalente,
reescrever 62 modelos e revisar 30 `@api.expect`. É semanas de trabalho e
uma mudança no Swagger publicado para corrigir três linhas.

**2. Três `@api.expect` validam de verdade.** `dashboard_controller.py:41`,
`notificacao_controller.py:33` e `ocorrencia_controller.py:55` passam
`validate=True`. Nesses, o modelo do flask-restx não é documentação, é
validação em runtime. Qualquer unificação precisa tratá-los como código de
comportamento, e é fácil não perceber isso.

**3. Os dois lados têm públicos diferentes.** O contract descreve o que a API
promete e vira Swagger. O schema descreve o que a API aceita e roda. Hoje eles
divergem por descuido, e a divergência é barata de detectar.

## O que fazer no lugar

`tests/integration/test_contracts_sem_campos_fantasma.py` fixa os três casos
corrigidos e guarda o escopo: um teste falha se a contagem de `validate=True`
mudar, obrigando a revisitar esta decisão quando alguém mover um modelo de
doc-only para validação.

Se a deriva voltar a crescer, o passo seguinte é um teste table-driven que
compare todos os 22 pares de uma vez, no formato do `test_authz_error_contract`
do S2. O script da auditoria está no histórico deste PR e serve de base.

Vale registrar uma armadilha para quem escrever esse teste: um regex ingênuo
que procure o corpo do `api.model` engole o modelo vizinho quando a formatação
muda. Na auditoria isso gerou 3 falsos positivos em 6, e só apareceu porque eu
fui conferir cada caso no arquivo antes de editar.

## Consequências

`api/contracts` e `app/schemas` seguem separados e mantidos à mão. O R5 fecha
com a deriva zerada, e o R12 fecha com esta recomendação. A pergunta 3 do plano
("unificar contracts e schemas?") passa a ter resposta: não, e o motivo está
aqui.
