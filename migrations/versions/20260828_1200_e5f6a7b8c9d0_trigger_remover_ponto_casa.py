"""trigger para remover o ponto de casa junto com o aluno (issue #76)

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-28 12:00:00.000000+00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


FUNCTION = """
CREATE OR REPLACE FUNCTION remover_ponto_casa_do_aluno() RETURNS TRIGGER AS $$
BEGIN
    IF OLD.ponto_casa_id IS NULL THEN
        RETURN NULL;
    END IF;

    -- Só apaga o ponto se mais ninguém o usa. Referências de rota/viagem são
    -- RESTRICT (apagar levantaria erro e abortaria a exclusão do aluno) e
    -- instituicao.ponto_id é CASCADE (apagar o ponto apagaria a escola).
    -- As linhas de alunos_confirmados do próprio aluno saem por CASCADE, então
    -- não contam como uso.
    WITH removido AS (
    DELETE FROM ponto p
    WHERE p.id = OLD.ponto_casa_id
      AND NOT EXISTS (SELECT 1 FROM aluno a WHERE a.ponto_casa_id = p.id)
      AND NOT EXISTS (SELECT 1 FROM rota_ponto rp WHERE rp.ponto_id = p.id)
      AND NOT EXISTS (SELECT 1 FROM viagem_ponto vp WHERE vp.ponto_id = p.id)
      AND NOT EXISTS (SELECT 1 FROM instituicao i WHERE i.ponto_id = p.id)
      AND NOT EXISTS (
          SELECT 1 FROM alunos_confirmados ac
          WHERE ac.aluno_id <> OLD.usuario_id
            AND (ac.ponto_embarque_id = p.id OR ac.ponto_destino_id = p.id)
      )
    RETURNING p.id
    )
    -- O endereço (logradouro, número, CEP) pendura no ponto, não no aluno, e a
    -- FK é SET NULL: sem isto ele sobreviveria à exclusão da conta como linha
    -- órfã e inalcançável, com o endereço residencial de quem já saiu.
    DELETE FROM endereco e WHERE e.ponto_id IN (SELECT id FROM removido);

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
"""

TRIGGER = """
CREATE TRIGGER trg_remover_ponto_casa
AFTER DELETE ON aluno
FOR EACH ROW
EXECUTE FUNCTION remover_ponto_casa_do_aluno();
"""


def upgrade() -> None:
    op.execute(FUNCTION)
    op.execute(TRIGGER)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_remover_ponto_casa ON aluno")
    op.execute("DROP FUNCTION IF EXISTS remover_ponto_casa_do_aluno()")
