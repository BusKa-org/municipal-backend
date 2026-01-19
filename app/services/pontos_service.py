from app.models.geo import Ponto
from app.models.user import User
from app.models.base import db
from sqlalchemy.exc import IntegrityError

class PontosService:
    
    @staticmethod
    def list_all(user_id):
        user = User.query.get(user_id)
        if not user: return {"error": "User not found"}, 403
        
        pontos = Ponto.query.filter_by(prefeitura_id=user.prefeitura_id).all()
        return [p.to_dict() for p in pontos], 200

    @staticmethod
    def get_by_id(user_id, ponto_id):
        user = User.query.get(user_id)
        ponto = Ponto.query.get(ponto_id)
        
        if not ponto: return {"error": "Ponto não encontrado"}, 404
        
        if user.prefeitura_id != ponto.prefeitura_id:
            return {"error": "Acesso negado"}, 403
            
        return ponto.to_dict(), 200

    @staticmethod
    def create_ponto(user_id, data):
        user = User.query.get(user_id)
        if not user or str(user.role) not in ['GESTOR', 'MOTORISTA']:
            return {"error": "Permissão negada"}, 403

        if not data.get('latitude') or not data.get('longitude'):
            return {"error": "Lat/Lon são obrigatórios"}, 400

        novo_ponto = Ponto(
            prefeitura_id=user.prefeitura_id,
            apelido=data.get('apelido', 'Sem Nome'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude')
        )
        
        db.session.add(novo_ponto)
        db.session.commit()
        
        return novo_ponto.to_dict(), 201

    @staticmethod
    def update_ponto(user_id, ponto_id, data):
        user = User.query.get(user_id)
        if not user or str(user.role) != 'GESTOR':
            return {"error": "Apenas gestores editam pontos"}, 403

        ponto = Ponto.query.get(ponto_id)
        if not ponto: return {"error": "Ponto não encontrado"}, 404
        
        if ponto.prefeitura_id != user.prefeitura_id:
            return {"error": "Acesso negado"}, 403

        if 'apelido' in data: ponto.apelido = data['apelido']
        if 'latitude' in data: ponto.latitude = data['latitude']
        if 'longitude' in data: ponto.longitude = data['longitude']

        db.session.commit()
        return ponto.to_dict(), 200

    @staticmethod
    def delete_ponto(user_id, ponto_id):
        user = User.query.get(user_id)
        if not user or str(user.role) != 'GESTOR':
            return {"error": "Permissão negada"}, 403

        ponto = Ponto.query.get(ponto_id)
        if not ponto:
            return {"error": "Ponto não encontrado"}, 404
            
        if ponto.prefeitura_id != user.prefeitura_id:
             return {"error": "Acesso negado"}, 403

        try:
            db.session.delete(ponto)
            db.session.commit()
            return {"message": "Ponto removido com sucesso"}, 200
        except IntegrityError:
            db.session.rollback()

            return {"error": "Este ponto está sendo usado em uma rota e não pode ser excluído"}, 400