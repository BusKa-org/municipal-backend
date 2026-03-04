"""Trips (Viagem) service - trip management, student confirmations."""

import logging
from datetime import UTC, date, datetime
from typing import Any

from app.core.exceptions import (
    AppError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.core.transaction import transactional
from app.models.base import db
from app.models.enum import DiaDaSemana, SentidoViagem, StatusViagem, UserRole
from app.models.geo import Ponto
from app.models.rota import DiasOperacao, HorarioRota, Rota, RotaAluno, RotaPonto
from app.models.user import Aluno, User
from app.models.viagem import AlunosConfirmados, Viagem, ViagemPonto

logger = logging.getLogger(__name__)


def _get_dia_semana_enum(data_obj: date) -> DiaDaSemana:
    """Convert weekday (0=Monday) to DiaDaSemana enum."""
    dias_map = {
        0: DiaDaSemana.SEG,
        1: DiaDaSemana.TER,
        2: DiaDaSemana.QUA,
        3: DiaDaSemana.QUI,
        4: DiaDaSemana.SEX,
        5: DiaDaSemana.SAB,
        6: DiaDaSemana.DOM,
    }
    dia = dias_map.get(data_obj.weekday())
    if not dia:
        raise ValidationError("Data inválida para cálculo do dia da semana")
    return dia


def _popular_dados_da_viagem(viagem_obj: Viagem, rota_obj: Rota) -> None:
    """Helper function that copies students and stops from route to trip."""
    inscricoes = db.session.query(RotaAluno).filter_by(rota_id=rota_obj.id).all()

    # Batch load all alunos to avoid N+1 queries
    aluno_ids = [i.aluno_id for i in inscricoes]
    if aluno_ids:
        alunos = db.session.query(Aluno).filter(Aluno.usuario_id.in_(aluno_ids)).all()
        alunos_map = {a.usuario_id: a for a in alunos}
    else:
        alunos_map = {}

    for inscricao in inscricoes:
        aluno = alunos_map.get(inscricao.aluno_id)
        if not aluno:
            continue

        conf = AlunosConfirmados(
            viagem_id=viagem_obj.id,
            aluno_id=aluno.usuario_id,
            confirmacao=False,
            ponto_embarque_id=None,
            ponto_destino_id=None,
        )
        db.session.add(conf)

    pontos_rota = (
        db.session.query(RotaPonto).filter_by(rota_id=rota_obj.id).order_by(RotaPonto.ordem).all()
    )

    ordem_real = 1
    for pr in pontos_rota:
        vp = ViagemPonto(
            viagem_id=viagem_obj.id, ponto_id=pr.ponto_id, ordem=ordem_real, visitado=False
        )
        db.session.add(vp)
        ordem_real += 1


def get_proximas_viagens_aluno(user_id: str) -> list[Viagem]:
    """Returns upcoming scheduled trips for the logged student."""
    aluno = db.session.get(User, user_id)
    if not aluno or aluno.role != UserRole.ALUNO:
        raise ForbiddenError("Apenas alunos podem ver sua agenda de viagens")

    hoje = datetime.now(UTC).date()

    query = (
        db.session.query(Viagem)
        .join(HorarioRota, Viagem.horario_rota_id == HorarioRota.id)
        .join(Rota, HorarioRota.rota_id == Rota.id)
        .join(RotaAluno, Rota.id == RotaAluno.rota_id)
        .outerjoin(
            AlunosConfirmados,
            (AlunosConfirmados.viagem_id == Viagem.id) & (AlunosConfirmados.aluno_id == aluno.id),
        )
        .filter(
            RotaAluno.aluno_id == aluno.id,
            Viagem.status == StatusViagem.AGENDADA,
            Viagem.data >= hoje,
        )
        .order_by(Viagem.data.asc(), HorarioRota.horario_saida.asc())
    )

    viagens = query.all()

    return viagens


def confirmar_presenca_aluno(
    user_id: str, viagem_id: str, data: dict[str, Any]
) -> AlunosConfirmados:
    """Student confirms or cancels attendance."""
    aluno = db.session.get(Aluno, user_id)
    if not aluno:
        # fallback to role check (polymorphic table)
        aluno_user = db.session.get(User, user_id)
        if aluno_user and aluno_user.role == UserRole.ALUNO:
            aluno = db.session.get(Aluno, user_id)

    if not aluno:
        raise ForbiddenError("Aluno não encontrado")

    confirmacao: bool = data["confirmacao"]
    ponto_embarque_id = data.get("ponto_embarque_id")

    with transactional():
        viagem = db.session.get(Viagem, viagem_id)
        if not viagem:
            raise NotFoundError("Viagem não encontrada")

        registro = db.session.get(AlunosConfirmados, (viagem.id, aluno.usuario_id))

        if not registro:
            horario = db.session.get(HorarioRota, viagem.horario_rota_id)
            if not horario:
                raise NotFoundError("Horário da viagem não encontrado")

            inscricao = db.session.get(RotaAluno, (horario.rota_id, aluno.usuario_id))
            if not inscricao:
                raise ForbiddenError("Você não está inscrito na rota desta viagem")

            registro = AlunosConfirmados(
                viagem_id=viagem.id,
                aluno_id=aluno.usuario_id,
                confirmacao=False,
                ponto_embarque_id=None,
                ponto_destino_id=None,
            )
            db.session.add(registro)

        if confirmacao:
            horario = db.session.get(HorarioRota, viagem.horario_rota_id)
            if not horario:
                raise NotFoundError("Horário da viagem não encontrado")

            # schema already enforces ponto_embarque_id presence on confirmacao=True
            ponto_valido = (
                db.session.query(RotaPonto)
                .filter_by(rota_id=horario.rota_id, ponto_id=ponto_embarque_id)
                .first()
            )
            if not ponto_valido:
                raise NotFoundError("Ponto de embarque não encontrado na rota")

            ponto_destino_inferido = None
            if horario.sentido == SentidoViagem.IDA:
                if aluno.instituicao and aluno.instituicao.ponto_id:
                    ponto_destino_inferido = aluno.instituicao.ponto_id
            else:
                if aluno.ponto_casa_id:
                    ponto_destino_inferido = aluno.ponto_casa_id

            registro.confirmacao = True
            registro.ponto_embarque_id = ponto_embarque_id
            registro.ponto_destino_id = ponto_destino_inferido
        else:
            registro.confirmacao = False
            registro.ponto_embarque_id = None
            registro.ponto_destino_id = None

        return registro


def listar_pontos_embarque(user_id: str, viagem_id: str) -> list[dict]:
    """
    Retorna os pontos de embarque disponíveis para uma viagem específica.

    Raises: ForbiddenError, NotFoundError, AppError
    """
    aluno = db.session.get(User, user_id)
    if not aluno or aluno.role != UserRole.ALUNO:
        raise ForbiddenError("Acesso restrito a alunos")

    viagem = db.session.get(Viagem, viagem_id)
    if not viagem:
        raise NotFoundError("Viagem não encontrada")

    horario = db.session.get(HorarioRota, viagem.horario_rota_id)
    if not horario:
        raise AppError("Horário não encontrado", 500)

    inscricao = (
        db.session.query(RotaAluno).filter_by(rota_id=horario.rota_id, aluno_id=aluno.id).first()
    )

    if not inscricao:
        raise ForbiddenError("Você não está inscrito na rota desta viagem")

    pontos_query = (
        db.session.query(RotaPonto, Ponto)
        .join(Ponto, RotaPonto.ponto_id == Ponto.id)
        .filter(RotaPonto.rota_id == horario.rota_id)
        .order_by(RotaPonto.ordem)
        .all()
    )

    resultado = []
    for rp, ponto_obj in pontos_query:
        resultado.append(
            {
                "ponto_id": str(ponto_obj.id),
                "apelido": ponto_obj.apelido,
                "latitude": float(ponto_obj.latitude),
                "longitude": float(ponto_obj.longitude),
                "ordem": rp.ordem,
            }
        )

    return resultado


def gerar_viagem(user_id: str, data_input: dict) -> Viagem:
    """
    Gera UMA viagem para UMA rota específica (Modo Manual).

    Raises: ForbiddenError, NotFoundError, ValidationError, ConflictError, AppError
    """
    user = db.session.get(User, user_id)
    if not user or user.role not in (UserRole.GESTOR, UserRole.MOTORISTA):
        raise ForbiddenError("Permissão negada")

    rota_id = data_input.get("rota_id")
    data_viagem = data_input.get("data")
    if not data_viagem:
        raise ValidationError("Data é obrigatória")
    data_viagem = datetime.strptime(data_viagem, "%Y-%m-%d").date()

    rota = db.session.get(Rota, rota_id)
    if not rota:
        raise NotFoundError("Rota não encontrada")

    if rota.prefeitura_id != user.prefeitura_id:
        raise ForbiddenError("Acesso negado")

    dia_semana = _get_dia_semana_enum(data_viagem)

    horario_selecionado = (
        db.session.query(HorarioRota)
        .join(DiasOperacao)
        .filter(HorarioRota.rota_id == rota.id, DiasOperacao.dia == dia_semana)
        .first()
    )
    if not horario_selecionado:
        raise NotFoundError(f"Horário não encontrado para a rota {rota.nome} no dia {dia_semana}")

    existente = (
        db.session.query(Viagem.id)
        .filter_by(data=data_viagem, horario_rota_id=horario_selecionado.id)
        .first()
    )
    if existente:
        raise ConflictError(
            f"Viagem já gerada para este dia/horário: {data_viagem} {horario_selecionado.horario_saida.strftime('%H:%M')}"
        )

    with transactional():
        nova_viagem = Viagem(
            data=data_viagem,
            horario_rota_id=horario_selecionado.id,
            motorista_id=rota.motorista_padrao_id,
            veiculo_id=rota.veiculo_padrao_id,
            status=StatusViagem.AGENDADA,
        )
        db.session.add(nova_viagem)
        db.session.flush()  # ensure nova_viagem.id

        _popular_dados_da_viagem(nova_viagem, rota)

        return nova_viagem


def gerar_viagens_em_lote(user_id: str, data_viagem: date) -> dict[str, Any]:
    """Batch create trips for all routes of a prefeitura on a specific date."""
    user = db.session.get(User, user_id)
    if not user or user.role != UserRole.GESTOR:
        raise ForbiddenError("Permissão negada. Apenas gestores podem gerar lote.")

    dia_semana = _get_dia_semana_enum(data_viagem)
    rotas = db.session.query(Rota).filter(Rota.prefeitura_id == user.prefeitura_id).all()

    relatorio: dict[str, Any] = {
        "total_rotas_analisadas": len(rotas),
        "viagens_criadas": 0,
        "detalhes": [],
    }

    with transactional():
        for rota in rotas:
            horarios_validos = (
                db.session.query(HorarioRota)
                .join(DiasOperacao)
                .filter(HorarioRota.rota_id == rota.id, DiasOperacao.dia == dia_semana)
                .all()
            )

            for horario in horarios_validos:
                existe = (
                    db.session.query(Viagem.id)
                    .filter_by(data=data_viagem, horario_rota_id=horario.id)
                    .first()
                )
                if existe:
                    continue

                nova_viagem = Viagem(
                    data=data_viagem,
                    horario_rota_id=horario.id,
                    motorista_id=rota.motorista_padrao_id,
                    veiculo_id=rota.veiculo_padrao_id,
                    status=StatusViagem.AGENDADA,
                )
                db.session.add(nova_viagem)
                db.session.flush()

                _popular_dados_da_viagem(nova_viagem, rota)

                relatorio["viagens_criadas"] += 1
                relatorio["detalhes"].append(
                    f"Viagem criada: {rota.nome} - {horario.horario_saida}"
                )

        return relatorio


def list_viagens_motorista(user_id: str) -> list[Viagem]:
    """List trips assigned to the driver."""
    return (
        db.session.query(Viagem).filter_by(motorista_id=user_id).order_by(Viagem.data.desc()).all()
    )


def controlar_viagem(user_id: str, viagem_id: str, data: dict[str, Any]) -> Viagem:
    """Start or finish a trip. Expects schema-validated payload with 'acao'."""
    user = db.session.get(User, user_id)
    viagem = db.session.get(Viagem, viagem_id)

    if not user:
        raise NotFoundError("Usuário não encontrado")

    if not viagem:
        raise NotFoundError("Viagem não encontrada")

    if user.role == UserRole.MOTORISTA and viagem.motorista_id != user.id:
        raise ForbiddenError("Esta viagem não pertence a você")

    acao = data.get("acao")

    with transactional():
        if acao == "INICIAR":
            if viagem.status != StatusViagem.AGENDADA:
                raise ValidationError(
                    f"Não é possível iniciar viagem com status {viagem.status.name}"
                )
            viagem.status = StatusViagem.EM_ANDAMENTO
            viagem.inicio_real = datetime.now(UTC)

        elif acao == "FINALIZAR":
            if viagem.status != StatusViagem.EM_ANDAMENTO:
                raise ValidationError("A viagem precisa estar em andamento para ser finalizada")
            viagem.status = StatusViagem.FINALIZADA
            viagem.fim_real = datetime.now(UTC)

        return viagem


def list_viagens_gestor(user_id: str, filters: dict[str, Any]) -> list[Viagem]:
    user = db.session.get(User, user_id)
    if not user or user.role != UserRole.GESTOR:
        raise ForbiddenError("Apenas gestores podem acessar o histórico completo")

    query = (
        db.session.query(Viagem)
        .join(HorarioRota)
        .join(Rota)
        .filter(Rota.prefeitura_id == user.prefeitura_id)
    )

    if filters.get("data_inicio"):
        query = query.filter(Viagem.data >= filters.get("data_inicio"))

    if filters.get("data_fim"):
        query = query.filter(Viagem.data <= filters.get("data_fim"))

    if filters.get("status"):
        query = query.filter(Viagem.status == filters.get("status"))

    if filters.get("motorista_id"):
        query = query.filter(Viagem.motorista_id == filters.get("motorista_id"))

    if filters.get("rota_id"):
        query = query.filter(Rota.id == filters.get("rota_id"))

    return query.order_by(Viagem.data.desc(), Viagem.horario_rota_id).all()
