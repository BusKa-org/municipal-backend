import logging

from app.models.enum import UserRole
from app.models.user import User
from app.services.viagens_service import gerar_viagens_periodo

logger = logging.getLogger(__name__)


def job_gerar_viagens_semanais(app):
    """Job que roda no fim de semana para gerar a agenda."""
    with app.app_context():
        try:
            gestores = User.query.filter_by(role=UserRole.GESTOR).distinct(User.prefeitura_id).all()

            for gestor in gestores:
                gerar_viagens_periodo(gestor_id=str(gestor.id), dias_futuros=14)

        except Exception as e:
            logger.error(f"Erro crítico no job semanal: {e}")
