"""Student (Aluno) service - registration, profile management."""

import logging
from typing import Any, cast

from werkzeug.security import generate_password_hash

from app.core.exceptions import (
    AppError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.models.base import db
from app.models.enum import UserRole, UserStatus
from app.models.geo import Endereco, Instituicao, Ponto
from app.models.user import Aluno, User
from app.services.user_service import _get_gestor_or_403
from app.utils import audit_logger, validate_cpf, validate_email, validate_password

logger = logging.getLogger(__name__)


def auto_cadastro(data: dict[str, Any]) -> Aluno:
    """
    Aluno se cadastra sozinho.
    A prefeitura é inferida através da Instituição escolhida.

    Returns: Aluno object
    Raises: NotFoundError, ValidationError, AppError
    """
    inst_id = data.get("instituicao_id")
    instituicao = db.session.get(Instituicao, inst_id)
    if not instituicao:
        raise NotFoundError("Instituição não encontrada")

    prefeitura_id = instituicao.ponto.prefeitura_id
    if not prefeitura_id:
        raise NotFoundError("Prefeitura não encontrada")

    email = validate_email(data.get("email", ""))
    cpf_clean = validate_cpf(data.get("cpf", ""))

    if db.session.query(User).filter((User.email == email) | (User.cpf == cpf_clean)).first():
        raise ConflictError("Email ou CPF já cadastrado")

    try:
        end_data = data.get("endereco_casa")
        if not end_data:
            raise ValidationError(
                "Endereço de casa é obrigatório", details={"field": "endereco_casa"}
            )

        password = validate_password(data.get("password", ""))

        ponto_casa = Ponto(
            prefeitura_id=prefeitura_id,
            latitude=end_data.get("latitude"),
            longitude=end_data.get("longitude"),
            apelido=f"Casa: {data.get('nome')}",
        )
        db.session.add(ponto_casa)
        db.session.flush()

        novo_end = Endereco(
            logradouro=end_data.get("logradouro"),
            numero=end_data.get("numero"),
            bairro=end_data.get("bairro"),
            cidade=end_data.get("cidade"),
            cep=end_data.get("cep"),
            ponto_id=ponto_casa.id,
        )
        db.session.add(novo_end)

        novo_aluno = Aluno(
            prefeitura_id=prefeitura_id,
            nome=data.get("nome"),
            email=data.get("email"),
            senha_hash=generate_password_hash(password),
            cpf=data.get("cpf"),
            telefone=data.get("telefone"),
            role=UserRole.ALUNO,
            matricula=data.get("matricula"),
            instituicao_id=instituicao.id,
            ponto_casa_id=ponto_casa.id,
            nome_pai=data.get("nome_pai"),
            cpf_pai=data.get("cpf_pai"),
            nome_mae=data.get("nome_mae"),
            cpf_mae=data.get("cpf_mae"),
        )

        db.session.add(novo_aluno)
        db.session.commit()

        return novo_aluno

    except AppError:
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating student: {e}")
        raise AppError(f"Erro ao criar aluno: {str(e)}", 500)


def update_me(user_id: str, data: dict[str, Any]) -> Aluno:
    """
    Atualiza perfil do aluno.

    Returns: Aluno object
    Raises: NotFoundError, AppError
    """
    aluno = db.session.get(Aluno, user_id)
    if not aluno:
        raise NotFoundError("Aluno não encontrado")

    try:
        # Update simple fields
        for field in (
            "nome",
            "telefone",
            "matricula",
            "nome_pai",
            "cpf_pai",
            "nome_mae",
            "cpf_mae",
        ):
            if field in data:
                setattr(aluno, field, data[field])

        if "endereco_casa" in data:
            end_data = data["endereco_casa"]

            if aluno.ponto_casa:
                ponto_casa = cast(Ponto, aluno.ponto_casa)
                ponto_casa.latitude = end_data.get("latitude")
                ponto_casa.longitude = end_data.get("longitude")
                if "nome" in data:
                    ponto_casa.apelido = f"Casa: {data['nome']}"

                endereco_bd = Endereco.query.filter_by(ponto_id=aluno.ponto_casa_id).first()

                if endereco_bd:
                    endereco_bd.logradouro = end_data.get("logradouro")
                    endereco_bd.numero = end_data.get("numero")
                    endereco_bd.bairro = end_data.get("bairro")
                    endereco_bd.cidade = end_data.get("cidade")
                    endereco_bd.cep = end_data.get("cep")
                else:
                    novo_end = Endereco(
                        ponto_id=aluno.ponto_casa_id,
                        logradouro=end_data.get("logradouro"),
                        numero=end_data.get("numero"),
                        bairro=end_data.get("bairro"),
                        cidade=end_data.get("cidade"),
                        cep=end_data.get("cep"),
                    )
                    db.session.add(novo_end)
            else:
                novo_ponto = Ponto(
                    prefeitura_id=aluno.prefeitura_id,
                    latitude=end_data.get("latitude"),
                    longitude=end_data.get("longitude"),
                    apelido=f"Casa: {data.get('nome', aluno.nome)}",
                )
                db.session.add(novo_ponto)
                db.session.flush()

                novo_end = Endereco(
                    ponto_id=novo_ponto.id,
                    logradouro=end_data.get("logradouro"),
                    numero=end_data.get("numero"),
                    bairro=end_data.get("bairro"),
                    cidade=end_data.get("cidade"),
                    cep=end_data.get("cep"),
                )
                db.session.add(novo_end)

                aluno.ponto_casa_id = novo_ponto.id

        if aluno.status == UserStatus.PENDING_SIGNUP:
            missing = []
            if not aluno.matricula and not data.get("matricula"):
                missing.append("matricula")
            if not aluno.instituicao_id and not data.get("instituicao_id"):
                missing.append("instituicao_id")
            end_data = data.get("endereco_casa")
            if (
                not end_data
                or end_data.get("latitude") is None
                or end_data.get("longitude") is None
            ):
                missing.append("endereco_casa.latitude/longitude")

            if missing:
                raise ValidationError(
                    "Cadastro precisa ser finalizado antes de usar o app",
                    details={"missing": missing},
                )

            aluno.status = UserStatus.ACTIVE
            aluno.signup_completed_at = db.func.now()
            audit_logger.log_user_action(
                action="complete_signup",
                user_id=user_id,
                resource_type="aluno",
                resource_id=user_id,
            )

        db.session.commit()
        return aluno

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating student profile: {e}")
        raise AppError(f"Erro ao atualizar perfil: {str(e)}", 500)


def delete_me(user_id: str) -> None:
    """
    Aluno se auto-exclui.

    Raises: NotFoundError, AppError
    """
    aluno = db.session.get(Aluno, user_id)
    if not aluno:
        raise NotFoundError("Aluno não encontrado")

    try:
        if aluno.ponto_casa:
            db.session.delete(aluno.ponto_casa)

        db.session.delete(aluno)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting student account: {e}")
        raise AppError(f"Erro ao excluir conta: {str(e)}", 500)


def list_alunos_gestor(gestor_id: str) -> list[Aluno]:
    """
    Lista alunos da prefeitura (apenas para gestores).

    Returns: List of Aluno objects
    Raises: ForbiddenError
    """
    gestor = _get_gestor_or_403(gestor_id, "Apenas gestores podem listar alunos")
    return db.session.query(Aluno).filter_by(prefeitura_id=gestor.prefeitura_id).all()
