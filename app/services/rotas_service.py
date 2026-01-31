"""Routes (Rota) service - route management, subscriptions, schedules."""

import logging
from typing import Any

from app.core.exceptions import (
    AppError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.models.base import db
from app.models.enum import DiaDaSemana, SentidoViagem, UserRole
from app.models.geo import Ponto
from app.models.rota import DiasOperacao, HorarioRota, Rota, RotaAluno, RotaPonto
from app.models.user import User

logger = logging.getLogger(__name__)


def list_all_rotas(user_id: str) -> list[Rota]:
    """List all routes for user's prefeitura."""
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")

    return Rota.query.filter_by(prefeitura_id=user.prefeitura_id).all()


def list_my_rotas(user_id: str) -> list[Rota]:
    """List routes linked to the logged-in user."""
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")

    match user.role:
        case UserRole.ALUNO:
            inscricoes = RotaAluno.query.filter_by(aluno_id=user.id).all()
            rota_ids = [i.rota_id for i in inscricoes]
            return Rota.query.filter(Rota.id.in_(rota_ids)).all()
        case UserRole.MOTORISTA:
            return Rota.query.filter_by(motorista_padrao_id=user.id).all()
        case UserRole.GESTOR:
            return Rota.query.filter_by(prefeitura_id=user.prefeitura_id).all()
        case _:
            return []


def gerenciar_inscricao_aluno(user_id: str, rota_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """
    Manage student subscription to a route.

    Raises: ForbiddenError, NotFoundError, ValidationError
    """
    aluno = db.session.get(User, user_id)
    if not aluno or str(getattr(aluno, "role", "")) != "ALUNO":
        raise ForbiddenError("Apenas alunos podem se inscrever")

    rota = db.session.get(Rota, rota_id)
    if not rota:
        raise NotFoundError("Rota não encontrada")

    acao = data.get("acao")
    if not acao or acao not in ["inscrever", "desinscrever"]:
        raise ValidationError("Ação inválida. Use 'inscrever' ou 'desinscrever'.")

    inscricao_existente = RotaAluno.query.filter_by(rota_id=rota.id, aluno_id=aluno.id).first()

    try:
        if acao == "inscrever":
            if inscricao_existente:
                return {"message": "Aluno já inscrito nesta rota"}

            nova_inscricao = RotaAluno(rota_id=rota.id, aluno_id=aluno.id)
            db.session.add(nova_inscricao)
            db.session.commit()
            return {"message": "Inscrição realizada com sucesso"}

        else:  # unsubscribe
            if not inscricao_existente:
                raise NotFoundError("Aluno não está inscrito nesta rota")

            db.session.delete(inscricao_existente)
            db.session.commit()
            return {"message": "Inscrição removida com sucesso"}

    except NotFoundError:
        raise
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error managing subscription: {e}")
        raise AppError(f"Erro ao gerenciar inscrição: {str(e)}", 500)


def create_rota(gestor_id: str, data: dict[str, Any]) -> Rota:
    """
    Create a new route with optional points and schedules.

    Raises: ForbiddenError, ValidationError, AppError
    """
    user = db.session.get(User, gestor_id)
    if not user or user.role not in (UserRole.GESTOR, UserRole.MOTORISTA):
        raise ForbiddenError("Permissão negada")

    nome = data.get("nome")
    if not nome:
        raise ValidationError("Nome da rota é obrigatório")

    try:
        # If a driver creates a route, automatically assign themselves as the default driver
        motorista_id = data.get("motorista_padrao_id")
        if not motorista_id and user.role == UserRole.MOTORISTA:
            motorista_id = user.id

        rota = Rota(
            nome=nome,
            motorista_padrao_id=motorista_id,
            veiculo_padrao_id=data.get("veiculo_padrao_id"),
            prefeitura_id=user.prefeitura_id,
        )

        db.session.add(rota)
        db.session.flush()

        if "pontos" in data:
            for p_data in data["pontos"]:
                if "latitude" not in p_data or "longitude" not in p_data:
                    continue
                novo_ponto = Ponto(
                    prefeitura_id=user.prefeitura_id,
                    latitude=p_data["latitude"],
                    longitude=p_data["longitude"],
                    apelido=p_data.get("apelido", f"Ponto {p_data.get('ordem')}"),
                )
                db.session.add(novo_ponto)
                db.session.flush()

                rota_ponto = RotaPonto(
                    rota_id=rota.id,
                    ponto_id=novo_ponto.id,
                    ordem=p_data.get("ordem", 0),
                )
                db.session.add(rota_ponto)

        if "horarios" in data:
            for h_data in data["horarios"]:
                novo_horario = HorarioRota(
                    rota_id=rota.id,
                    horario_saida=h_data["horario_saida"],
                    sentido=h_data["sentido"],
                )
                db.session.add(novo_horario)
                db.session.flush()

                dias_list = h_data.get("dias", [])
                for dia_str in dias_list:
                    if dia_str in ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"]:
                        novo_dia = DiasOperacao(horario_rota_id=novo_horario.id, dia=dia_str)
                        db.session.add(novo_dia)

        db.session.commit()
        return rota

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating route: {e}")
        raise AppError(f"Erro ao criar rota: {str(e)}", 500)


def add_ponto(gestor_id: str, rota_id: str, data: dict[str, Any]) -> None:
    """
    Add points to a route.

    Raises: ForbiddenError, NotFoundError, ValidationError, AppError
    """
    user = User.query.get(gestor_id)

    if not user or user.role not in (UserRole.GESTOR, UserRole.MOTORISTA):
        raise ForbiddenError("Permissão negada")

    rota = Rota.query.get(rota_id)
    if not rota:
        raise NotFoundError("Rota não encontrada")

    if rota.prefeitura_id != user.prefeitura_id:
        raise ForbiddenError("Acesso negado")

    pontos = data.get("pontos", [])
    if not pontos or not isinstance(pontos, list):
        raise ValidationError("A rota deve conter pelo menos um ponto válido")

    try:
        # Clear existing route points (replacing with new set)
        RotaPonto.query.filter_by(rota_id=rota.id).delete()
        db.session.flush()

        for p in pontos:
            ponto_id = p.get("ponto_id")
            ordem = p.get("ordem", 1)

            # Case 1: Link existing point by ID
            if ponto_id:
                existing_ponto = Ponto.query.get(ponto_id)
                if not existing_ponto:
                    logger.warning(f"Point {ponto_id} not found, skipping")
                    continue
                if existing_ponto.prefeitura_id != rota.prefeitura_id:
                    logger.warning(f"Point {ponto_id} belongs to different prefeitura, skipping")
                    continue

                novo_rota_ponto = RotaPonto(rota_id=rota.id, ponto_id=ponto_id, ordem=ordem)
                db.session.add(novo_rota_ponto)

            # Case 2: Create new point with coordinates
            else:
                nome_p = p.get("nome")
                lat = p.get("latitude")
                lon = p.get("longitude")

                if not nome_p or lat is None or lon is None:
                    continue

                ponto = Ponto(
                    prefeitura_id=rota.prefeitura_id,
                    apelido=nome_p,
                    latitude=lat,
                    longitude=lon,
                )
                db.session.add(ponto)
                db.session.flush()

                novo_rota_ponto = RotaPonto(rota_id=rota.id, ponto_id=ponto.id, ordem=ordem)
                db.session.add(novo_rota_ponto)

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding points to route: {e}")
        raise AppError(f"Erro ao adicionar pontos: {str(e)}", 500)


def add_horario(gestor_id: str, rota_id: str, data: dict[str, Any]) -> HorarioRota:
    """
    Add a schedule to a route.

    Raises: ForbiddenError, NotFoundError, ValidationError, AppError
    """
    user = User.query.get(gestor_id)
    if not user or user.role != UserRole.GESTOR:
        raise ForbiddenError("Apenas gestores gerenciam horários")

    rota = Rota.query.get(rota_id)
    if not rota:
        raise NotFoundError("Rota não encontrada")

    if rota.prefeitura_id != user.prefeitura_id:
        raise ForbiddenError("Acesso negado")

    dias_list = data.get("dias", [])
    if not dias_list:
        raise ValidationError("Selecione pelo menos um dia da semana")

    try:
        novo_horario = HorarioRota(
            rota_id=rota.id,
            horario_saida=data.get("horario_saida"),
            sentido=SentidoViagem(data.get("sentido")),
        )
        db.session.add(novo_horario)
        db.session.flush()

        for dia_str in dias_list:
            novo_dia = DiasOperacao(horario_rota_id=novo_horario.id, dia=DiaDaSemana(dia_str))
            db.session.add(novo_dia)

        db.session.commit()
        return novo_horario

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding schedule: {e}")
        raise AppError(f"Erro ao adicionar horário: {str(e)}", 500)


def get_horarios(user_id: str, rota_id: str) -> list:
    """
    Get schedules for a route.

    Raises: NotFoundError, ForbiddenError
    """
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")

    rota = Rota.query.get(rota_id)
    if not rota:
        raise NotFoundError("Rota não encontrada")

    if (
        user.role in (UserRole.GESTOR, UserRole.MOTORISTA)
        and rota.prefeitura_id != user.prefeitura_id
    ):
        raise ForbiddenError("Acesso negado")

    return rota.grade_horarios


def get_by_id(user_id: str, rota_id: str) -> Rota:
    """
    Get route by ID.

    Raises: NotFoundError, ForbiddenError
    """
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")

    rota = Rota.query.get(rota_id)
    if not rota:
        raise NotFoundError("Rota não encontrada")

    if (
        user.role in (UserRole.GESTOR, UserRole.MOTORISTA)
        and rota.prefeitura_id != user.prefeitura_id
    ):
        raise ForbiddenError("Acesso negado")

    return rota


def update_rota(user_id: str, rota_id: str, data: dict[str, Any]) -> Rota:
    """
    Update route name, driver, or vehicle.

    Raises: ForbiddenError, NotFoundError, AppError
    """
    user = User.query.get(user_id)

    if not user or user.role != UserRole.GESTOR:
        raise ForbiddenError("Permissão negada")

    rota = Rota.query.get(rota_id)
    if not rota:
        raise NotFoundError("Rota não encontrada")

    if rota.prefeitura_id != user.prefeitura_id:
        raise ForbiddenError("Acesso negado")

    try:
        if "nome" in data:
            rota.nome = data.get("nome")

        if "motorista_id" in data:
            rota.motorista_padrao_id = data.get("motorista_id")

        if "veiculo_id" in data:
            rota.veiculo_padrao_id = data.get("veiculo_id")

        db.session.commit()
        return rota

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating route: {e}")
        raise AppError(f"Erro ao atualizar rota: {str(e)}", 500)


def delete_rota(user_id: str, rota_id: str) -> None:
    """
    Delete a route.

    Raises: ForbiddenError, NotFoundError, AppError
    """
    user = User.query.get(user_id)

    if not user or user.role != UserRole.GESTOR:
        raise ForbiddenError("Permissão negada")

    rota = Rota.query.get(rota_id)
    if not rota:
        raise NotFoundError("Rota não encontrada")

    if rota.prefeitura_id != user.prefeitura_id:
        raise ForbiddenError("Acesso negado")

    try:
        db.session.delete(rota)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting route: {e}")
        raise AppError(f"Erro ao remover rota: {str(e)}", 500)


def get_pontos_by_rota(user_id: str, rota_id: str) -> list[dict[str, Any]]:
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")

    rota = Rota.query.get(rota_id)
    if not rota:
        raise NotFoundError("Rota não encontrada")

    rota_pontos = RotaPonto.query.filter_by(rota_id=rota_id).order_by(RotaPonto.ordem.asc()).all()

    resultado = []
    for rp in rota_pontos:
        ponto = rp.ponto
        resultado.append(
            {
                "id": str(ponto.id),
                "apelido": ponto.apelido,
                "latitude": float(ponto.latitude),
                "longitude": float(ponto.longitude),
                "ordem": rp.ordem,
            }
        )

    return resultado
