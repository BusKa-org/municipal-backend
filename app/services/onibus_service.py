import logging
from typing import Any

from app.models.onibus import Onibus
from app.models.user import User
from app.models.base import db
from app.core.exceptions import (
    AppError, NotFoundError, ValidationError, ForbiddenError, ConflictError
)

logger = logging.getLogger(__name__)


class OnibusService:
    
    @staticmethod
    def list_all(user_id: str) -> list[Onibus]:
        """List all buses for user's prefeitura."""
        user = User.query.get(user_id)
        if not user:
            raise NotFoundError("Usuário não encontrado")

        return Onibus.query.filter_by(prefeitura_id=user.prefeitura_id).all()

    @staticmethod
    def get_by_id(user_id: str, onibus_id: str) -> Onibus:
        """
        Get bus by ID (with tenant check).
        
        Raises: NotFoundError, ForbiddenError
        """
        user = User.query.get(user_id)
        if not user:
            raise NotFoundError("Usuário não encontrado")

        onibus = Onibus.query.get(onibus_id)
        if not onibus:
            raise NotFoundError("Ônibus não encontrado")
            
        if onibus.prefeitura_id != user.prefeitura_id:
            raise ForbiddenError("Acesso negado a este recurso")

        return onibus

    @staticmethod
    def create_onibus(user_id: str, data: dict[str, Any]) -> Onibus:
        """
        Create a new bus (gestor only).
        
        Raises: ForbiddenError, ValidationError, ConflictError, AppError
        """
        user = User.query.get(user_id)
        
        if not user or str(user.role) != 'GESTOR':
            raise ForbiddenError("Apenas gestores podem gerenciar a frota")

        placa = data.get("placa", "").upper().strip()
        modelo = data.get("modelo", "").strip()
        capacidade = data.get("capacidade")

        if not placa or not capacidade:
            raise ValidationError("Placa e Capacidade são obrigatórios")

        if Onibus.query.filter_by(placa=placa).first():
            raise ConflictError(f"Já existe um ônibus com a placa {placa}")

        try:
            novo_onibus = Onibus(
                placa=placa,
                modelo=modelo,
                capacidade=capacidade,
                prefeitura_id=user.prefeitura_id 
            )
            db.session.add(novo_onibus)
            db.session.commit()
            return novo_onibus
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating bus: {e}")
            raise AppError(f"Erro ao salvar ônibus: {str(e)}", 500)

    @staticmethod
    def delete_onibus(user_id: str, onibus_id: str) -> None:
        """
        Delete a bus (gestor only).
        
        Raises: ForbiddenError, NotFoundError, AppError
        """
        user = User.query.get(user_id)
        
        if not user or str(user.role) != 'GESTOR':
            raise ForbiddenError("Apenas gestores podem gerenciar a frota")

        onibus = Onibus.query.get(onibus_id)
        if not onibus:
            raise NotFoundError("Ônibus não encontrado")
        
        if onibus.prefeitura_id != user.prefeitura_id:
            raise ForbiddenError("Proibido alterar dados de outra prefeitura")

        try:
            db.session.delete(onibus)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting bus: {e}")
            raise AppError("Não é possível remover este veículo pois ele possui viagens vinculadas", 400)