from app.models.onibus import Onibus
from app.models.user import User
from app.models.base import db
from sqlalchemy.exc import IntegrityError
import uuid

class OnibusService:
    
    @staticmethod
    def list_all(user_id):
        """Lista apenas ônibus da prefeitura do usuário logado"""
        user = User.query.get(user_id)
        
        if not user:
            return {"error": "Usuário não encontrado"}, 403

        frota = Onibus.query.filter_by(prefeitura_id=user.prefeitura_id).all()
        return frota, 200

    @staticmethod
    def get_by_id(user_id, onibus_id):
        user = User.query.get(user_id)
        if not user:
            return {"error": "Usuário não encontrado"}, 403

        onibus = Onibus.query.get(onibus_id)
        if not onibus:
            return {"error": "Ônibus não encontrado"}, 404
            
        if onibus.prefeitura_id != user.prefeitura_id:
            return {"error": "Acesso negado a este recurso"}, 403

        return onibus, 200

    @staticmethod
    def create_onibus(user_id, data):
        user = User.query.get(user_id)
        
        if not user or str(user.role) != 'GESTOR':
            return {"error": "Apenas gestores podem gerenciar a frota"}, 403

        placa = data.get("placa", "").upper().strip()
        modelo = data.get("modelo", "").strip()
        capacidade = data.get("capacidade")

        if not placa or not capacidade:
            return {"error": "Placa e Capacidade são obrigatórios"}, 400

        if Onibus.query.filter_by(placa=placa).first():
            return {"error": f"Já existe um ônibus com a placa {placa}"}, 400

        novo_onibus = Onibus(
            placa=placa,
            modelo=modelo,
            capacidade=capacidade,
            prefeitura_id=user.prefeitura_id 
        )

        try:
            db.session.add(novo_onibus)
            db.session.commit()
            return novo_onibus, 201
        except IntegrityError:
            db.session.rollback()
            return {"error": "Erro ao salvar no banco"}, 400

    @staticmethod
    def delete_onibus(user_id, onibus_id):
        user = User.query.get(user_id)
        
        if not user or str(user.role) != 'GESTOR':
            return {"error": "Proibido"}, 403

        onibus = Onibus.query.get(onibus_id)
        if not onibus:
            return {"error": "Ônibus não encontrado"}, 404
        
        if onibus.prefeitura_id != user.prefeitura_id:
            return {"error": "Proibido alterar dados de outra prefeitura"}, 403

        try:
            db.session.delete(onibus)
            db.session.commit()
            return {"message": "Ônibus removido com sucesso"}, 200
        except IntegrityError:
            db.session.rollback()
            return {"error": "Não é possível remover este veículo pois ele possui viagens vinculadas"}, 400