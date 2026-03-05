"""Trips (Viagem) service - trip management, student confirmations."""

import logging
from datetime import datetime
from typing import Any

from app.core.exceptions import (
    AppError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.models.base import db
from app.models.enum import SentidoViagem, StatusViagem, UserRole
from app.models.geo import Ponto
from app.models.rota import DiasOperacao, HorarioRota, Rota, RotaAluno, RotaPonto
from app.models.user import Aluno, User
from app.models.viagem import AlunosConfirmados, Viagem, ViagemPonto

logger = logging.getLogger(__name__)


def _get_dia_semana_enum(data_obj):
    """Convert weekday (0=Monday) to DiaDaSemana enum."""
    dias_map = {0: "SEG", 1: "TER", 2: "QUA", 3: "QUI", 4: "SEX", 5: "SAB", 6: "DOM"}
    return dias_map.get(data_obj.weekday())


def _popular_dados_da_viagem(viagem_obj, rota_obj, horario_obj):
    """Helper function that copies students and stops from route to trip."""
    inscricoes = RotaAluno.query.filter_by(rota_id=rota_obj.id).all()

    # Batch load all alunos to avoid N+1 queries
    aluno_ids = [i.aluno_id for i in inscricoes]
    alunos_map = {
        a.usuario_id: a for a in Aluno.query.filter(Aluno.usuario_id.in_(aluno_ids)).all()
    }

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

    pontos_rota = RotaPonto.query.filter_by(rota_id=rota_obj.id).order_by(RotaPonto.ordem).all()

    ordem_real = 1
    for pr in pontos_rota:
        vp = ViagemPonto(
            viagem_id=viagem_obj.id, ponto_id=pr.ponto_id, ordem=ordem_real, visitado=False
        )
        db.session.add(vp)
        ordem_real += 1


def get_proximas_viagens_aluno(user_id: str) -> list[dict]:
    """
    Retorna as próximas viagens agendadas para o aluno logado.

    Raises: ForbiddenError
    """
    aluno = db.session.get(User, user_id)
    if not aluno or aluno.role != UserRole.ALUNO:
        raise ForbiddenError("Apenas alunos podem ver sua agenda de viagens")

    hoje = datetime.utcnow().date()

    query = (
        db.session.query(Viagem, HorarioRota, Rota, AlunosConfirmados)
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

    resultados = query.all()

    agenda = []
    for viagem, horario, rota, confirmacao in resultados:
        status_conf = confirmacao.confirmacao if confirmacao else False
        ponto_emb = (
            str(confirmacao.ponto_embarque_id)
            if (confirmacao and confirmacao.ponto_embarque_id)
            else None
        )

        agenda.append(
            {
                "viagem_id": str(viagem.id),
                "data": str(viagem.data),
                "dia_semana": _get_dia_semana_enum(viagem.data),
                "horario_saida": str(horario.horario_saida),
                "sentido": horario.sentido.name,
                "rota_id": str(rota.id),
                "rota_nome": rota.nome,
                "status_confirmacao": status_conf,
                "ponto_embarque_id": ponto_emb,
            }
        )

    return agenda


def confirmar_presenca_aluno(user_id: str, viagem_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """
    Permite ao aluno confirmar participação.

    Raises: ForbiddenError, NotFoundError, ValidationError, AppError
    """
    aluno = db.session.get(Aluno, user_id)
    if not aluno:
        aluno_user = db.session.get(User, user_id)
        if aluno_user and aluno_user.role == UserRole.ALUNO:
            aluno = db.session.get(Aluno, user_id)

    if not aluno:
        raise ForbiddenError("Aluno não encontrado")

    viagem = db.session.get(Viagem, viagem_id)
    if not viagem:
        raise NotFoundError("Viagem não encontrada")

    registro = AlunosConfirmados.query.filter_by(
        viagem_id=viagem.id, aluno_id=aluno.usuario_id
    ).first()

    if not registro:
        horario_temp = db.session.get(HorarioRota, viagem.horario_rota_id)
        if not horario_temp:
            raise NotFoundError("Horário da viagem não encontrado")

        inscricao = RotaAluno.query.filter_by(
            rota_id=horario_temp.rota_id, aluno_id=aluno.usuario_id
        ).first()

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

    confirmacao = data.get("confirmacao")
    ponto_embarque_id = data.get("ponto_embarque_id")

    try:
        if confirmacao:
            if not ponto_embarque_id:
                raise ValidationError(
                    "Para confirmar, é necessário selecionar um ponto de embarque"
                )

            horario = db.session.get(HorarioRota, viagem.horario_rota_id)
            if not horario:
                raise NotFoundError("Horário da viagem não encontrado")

            ponto_valido = RotaPonto.query.filter_by(
                rota_id=horario.rota_id, ponto_id=ponto_embarque_id
            ).first()

            if not ponto_valido:
                raise ValidationError("Este ponto não pertence à rota desta viagem")

            ponto_destino_inferido = None

            if horario.sentido == SentidoViagem.IDA:
                if aluno.instituicao and aluno.instituicao.ponto_id:
                    ponto_destino_inferido = aluno.instituicao.ponto_id
            elif horario.sentido == SentidoViagem.VOLTA:
                if aluno.ponto_casa_id:
                    ponto_destino_inferido = aluno.ponto_casa_id

            registro.confirmacao = True
            registro.ponto_embarque_id = ponto_embarque_id
            registro.ponto_destino_id = ponto_destino_inferido
        else:
            registro.confirmacao = False
            registro.ponto_embarque_id = None
            registro.ponto_destino_id = None

        db.session.commit()

        status_str = "confirmada" if confirmacao else "cancelada"
        return {"message": f"Presença {status_str} com sucesso"}

    except (ValidationError, ForbiddenError):
        raise
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error confirming attendance: {e}")
        raise AppError(f"Erro ao confirmar presença: {str(e)}", 500)


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

    inscricao = RotaAluno.query.filter_by(rota_id=horario.rota_id, aluno_id=aluno.id).first()

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


def gerar_viagem(user_id: str, data_input: dict) -> dict:
    """
    Gera UMA viagem para UMA rota específica (Modo Manual).

    Raises: ForbiddenError, NotFoundError, ValidationError, ConflictError, AppError
    """
    user = db.session.get(User, user_id)
    if not user or user.role not in (UserRole.GESTOR, UserRole.MOTORISTA):
        raise ForbiddenError("Permissão negada")

    rota_id = data_input.get("rota_id")
    data_str = data_input.get("data")
    motorista_id = data_input.get("motorista_id")

    if not data_str:
        raise ValidationError("Campo 'data' é obrigatório")

    rota = db.session.get(Rota, rota_id)
    if not rota:
        raise NotFoundError("Rota não encontrada")

    if rota.prefeitura_id != user.prefeitura_id:
        raise ForbiddenError("Acesso negado")

    try:
        data_viagem = datetime.strptime(data_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ValidationError("Data inválida. Use YYYY-MM-DD")

    dia_semana = _get_dia_semana_enum(data_viagem)

    horario_selecionado = (
        db.session.query(HorarioRota)
        .join(DiasOperacao)
        .filter(HorarioRota.rota_id == rota.id, DiasOperacao.dia == dia_semana)
        .first()
    )

    if not horario_selecionado:
        raise ValidationError(f"Esta rota não opera em {dia_semana}")

    if Viagem.query.filter_by(data=data_viagem, horario_rota_id=horario_selecionado.id).first():
        raise ConflictError("Viagem já gerada para este dia/horário")

    try:
        nova_viagem = Viagem(
            data=data_viagem,
            horario_rota_id=horario_selecionado.id,
            motorista_id=motorista_id,
            veiculo_id=rota.veiculo_padrao_id,
            status=StatusViagem.AGENDADA,
        )
        db.session.add(nova_viagem)
        db.session.flush()

        _popular_dados_da_viagem(nova_viagem, rota, horario_selecionado)

        db.session.commit()

        return {
            "message": "Viagem gerada com sucesso",
            "id": str(nova_viagem.id),
            "dia": dia_semana,
        }

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error generating trip: {e}")
        raise AppError(f"Erro ao gerar viagem: {str(e)}", 500)


def gerar_viagens_em_lote(user_id: str, data_str: str) -> dict:
    """
    Gera viagens para TODAS as rotas da prefeitura em uma data específica.

    Raises: ForbiddenError, ValidationError, AppError
    """
    user = db.session.get(User, user_id)
    if not user or user.role != UserRole.GESTOR:
        raise ForbiddenError("Permissão negada. Apenas gestores podem gerar lote.")

    try:
        data_viagem = datetime.strptime(data_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError("Data inválida. Use YYYY-MM-DD")

    dia_semana = _get_dia_semana_enum(data_viagem)

    rotas = Rota.query.filter_by(prefeitura_id=user.prefeitura_id).all()

    relatorio: dict[str, Any] = {
        "total_rotas_analisadas": len(rotas),
        "viagens_criadas": 0,
        "detalhes": [],
    }

    try:
        for rota in rotas:
            horarios_validos = (
                db.session.query(HorarioRota)
                .join(DiasOperacao)
                .filter(HorarioRota.rota_id == rota.id, DiasOperacao.dia == dia_semana)
                .all()
            )

            if not horarios_validos:
                continue

            for horario in horarios_validos:
                if Viagem.query.filter_by(data=data_viagem, horario_rota_id=horario.id).first():
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

                _popular_dados_da_viagem(nova_viagem, rota, horario)

                relatorio["viagens_criadas"] += 1
                relatorio["detalhes"].append(
                    f"Viagem criada: {rota.nome} - {horario.horario_saida}"
                )

        db.session.commit()
        return relatorio

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error generating batch trips: {e}")
        raise AppError(f"Erro ao gerar viagens em lote: {str(e)}", 500)


def list_viagens_motorista(user_id: str) -> list[Viagem]:
    """List trips assigned to the driver."""
    return Viagem.query.filter_by(motorista_id=user_id).order_by(Viagem.data.desc()).all()


def controlar_viagem(user_id: str, viagem_id: str, data: dict[str, Any]) -> Viagem:
    """
    Inicia ou Finaliza viagem.

    Raises: NotFoundError, ForbiddenError, ValidationError, AppError
    """
    user = db.session.get(User, user_id)
    viagem = db.session.get(Viagem, viagem_id)

    if not user:
        raise NotFoundError("Usuário não encontrado")

    if not viagem:
        raise NotFoundError("Viagem não encontrada")

    if user.role == UserRole.MOTORISTA and viagem.motorista_id != user.id:
        raise ForbiddenError("Esta viagem não pertence a você")

    acao = data.get("acao")
    if not acao:
        raise ValidationError("Campo 'acao' obrigatório")

    try:
        if acao == "INICIAR":
            if viagem.status != StatusViagem.AGENDADA:
                raise ValidationError(
                    f"Não é possível iniciar viagem com status {viagem.status.name}"
                )
            viagem.status = StatusViagem.EM_ANDAMENTO
            viagem.inicio_real = datetime.utcnow()

        elif acao == "FINALIZAR":
            if viagem.status != StatusViagem.EM_ANDAMENTO:
                raise ValidationError("A viagem precisa estar em andamento para ser finalizada")
            viagem.status = StatusViagem.FINALIZADA
            viagem.fim_real = datetime.utcnow()
        else:
            raise ValidationError("Ação inválida. Use INICIAR ou FINALIZAR")

        db.session.commit()
        return viagem

    except ValidationError:
        raise
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error controlling trip: {e}")
        raise AppError(f"Erro ao controlar viagem: {str(e)}", 500)


def list_viagens_gestor(user_id: str, filters: dict) -> list[Viagem]:
    """
    List all trips with filters (gestor only).

    Raises: ForbiddenError
    """
    user = db.session.get(User, user_id)
    if not user or user.role != UserRole.GESTOR:
        raise ForbiddenError("Apenas gestores podem acessar o histórico completo")

    query = Viagem.query
    query = query.join(HorarioRota).join(Rota)
    query = query.filter(Rota.prefeitura_id == user.prefeitura_id)

    if filters.get("data_inicio"):
        query = query.filter(Viagem.data >= filters.get("data_inicio"))

    if filters.get("data_fim"):
        query = query.filter(Viagem.data <= filters.get("data_fim"))

    if filters.get("status"):
        query = query.filter(Viagem.status == StatusViagem(filters.get("status")))

    if filters.get("motorista_id"):
        query = query.filter(Viagem.motorista_id == filters.get("motorista_id"))

    if filters.get("rota_id"):
        query = query.filter(Rota.id == filters.get("rota_id"))

    return query.order_by(Viagem.data.desc(), Viagem.horario_rota_id).all()
