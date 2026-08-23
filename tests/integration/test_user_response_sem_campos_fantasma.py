"""Resíduo da limpeza do PR #34: campos que a API anunciava e o banco
não tem mais.

O PR #34 corrigiu o cadastro que estourava ao passar `nome_pai`,
`nome_mae` e `salario` para construtores de `User`. As colunas foram removidas
por migração: `nome_pai` virou `nome_responsavel` e `nome_mae` foi apagada em
`d4e5f6a7b8c9`; `Gestor.matricula` e `Gestor.salario` saíram em `a1b2c3d4e5f6`.

O que sobrou foi a ponta de documentação: `UserResponseSchema` e
`user_contract` seguiam anunciando os três campos, que serializavam `null`
para sempre e apareciam no Swagger como se existissem.

Estes testes fixam o contrato depois da limpeza, e provam que os campos
polimórficos que **de fato** existem continuam saindo.
"""

import pytest

from app.schemas.user_schema import UserResponseSchema

pytestmark = pytest.mark.integration


def test_resposta_de_usuario_nao_anuncia_campos_removidos_por_migracao(_db, aluno):
    dump = UserResponseSchema().dump(aluno.user)

    assert "nome_pai" not in dump
    assert "nome_mae" not in dump
    assert "salario" not in dump


def test_campos_polimorficos_reais_continuam_saindo(_db, aluno, motorista):
    dump_aluno = UserResponseSchema().dump(aluno.user)
    dump_motorista = UserResponseSchema().dump(motorista.user)

    # `matricula` existe em Aluno e `cnh` existe em Motorista. Os dois seguem
    # declarados com `dump_default=None` porque a serialização é polimórfica.
    assert "matricula" in dump_aluno
    assert dump_motorista["cnh"] == motorista.user.cnh


def test_resposta_de_usuario_mantem_os_campos_de_sempre(_db, aluno):
    dump = UserResponseSchema().dump(aluno.user)

    assert dump["id"] == str(aluno.user.id)
    assert dump["nome"] == aluno.user.nome
    assert dump["email"] == aluno.user.email
    assert dump["role"] == aluno.user.role.value


def test_contrato_do_swagger_nao_lista_campos_removidos():
    import inspect

    from app.api.contracts import user_contract

    fonte = inspect.getsource(user_contract)
    assert "nome_pai" not in fonte
    assert "nome_mae" not in fonte
    assert "salario" not in fonte
