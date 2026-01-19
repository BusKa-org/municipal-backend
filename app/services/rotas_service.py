from datetime import datetime
from flask import request

from ..models.user import User
from ..models.geo import Ponto
from ..models.rota import Rota, RotaAluno, RotaPonto 
from ..models.base import db

class RotasService:
    
    @staticmethod
    def list_all_rotas(user_id):
        user = User.query.get(user_id)
        if not user:
            return {"error": "User nao existe"}, 403

        rotas = Rota.query.all()

        return ([
            {
                "id": r.id, 
                "nome": r.nome, 
                "motorista_id": r.motorista_padrao_id
            }
            for r in rotas
        ], 200)

    @staticmethod
    def list_my_rotas(user_id):
        user = User.query.get(user_id)
        if not user:
            return {"error": "User nao existe"}, 403

        rotas = []

        if str(user.role) == 'ALUNO':
            inscricoes = RotaAluno.query.filter_by(aluno_id=user.id).all()
            rota_ids = [i.rota_id for i in inscricoes]
            rotas = Rota.query.filter(Rota.id.in_(rota_ids)).all()

        elif str(user.role) == 'MOTORISTA':
            rotas = Rota.query.filter_by(motorista_padrao_id=user.id).all()

        elif str(user.role) == 'GESTOR':
            rotas = Rota.query.all()

        return ([
            {
                "id": r.id, 
                "nome": r.nome, 
                "motorista_id": r.motorista_padrao_id
            }
            for r in rotas
        ], 200)

    @staticmethod
    def inscricao_aluno_rota(user_id, rota_id):
        user = User.query.get(user_id)
        if not user or str(user.role) != 'ALUNO':
            return {"error": "Apenas alunos podem se inscrever"}, 403
    
        rota = Rota.query.get(rota_id)
        if not rota:
            return {"error": "Rota não encontrada"}, 404
    
        data = request.get_json()
        acao = data.get("acao", "").lower()
    
        if acao not in ["inscrever", "desinscrever"]:
            return {"error": "Ação inválida. Use 'inscrever' ou 'desinscrever'."}, 400
    
        inscricao = RotaAluno.query.filter_by(aluno_id=user.id, rota_id=rota.id).first()
    
        if acao == "inscrever":
            if inscricao:
                return {"message": "Aluno já inscrito nesta rota."}, 200

            nova_inscricao = RotaAluno(aluno_id=user.id, rota_id=rota.id)
            db.session.add(nova_inscricao)
            db.session.commit()
            return {"message": "Aluno inscrito na rota com sucesso."}, 200
    
        elif acao == "desinscrever":
            if not inscricao:
                return {"message": "Aluno não está inscrito nesta rota."}, 200

            db.session.delete(inscricao)
            db.session.commit()
            return {"message": "Aluno desinscrito da rota com sucesso."}, 200

    @staticmethod
    def create_rota(gestor_id, data):
        user = User.query.get(gestor_id)
        if not user or str(user.role) not in ['GESTOR', 'MOTORISTA']:
            return {"error": "Permissão negada"}, 403

        nome = data.get("nome")
        if not nome:
            return {"error": "Nome da rota é obrigatório"}, 400

        user_m_id = data.get("motorista_id")

        rota = Rota(
            nome=nome,
            motorista_padrao_id=user_m_id,
        )

        db.session.add(rota)
        db.session.commit()

        return ({
            "message": "Rota criada com sucesso",
            "rota": {
                "id": rota.id,
                "nome": rota.nome,
                "motorista_id": rota.motorista_padrao_id,
            }
        }, 201)

    @staticmethod
    def add_ponto(gestor_id, rota_id, data):
        user = User.query.get(gestor_id)
        
        if not user or str(user.role) not in ['GESTOR', 'MOTORISTA']:
            return {"error": "Permissão negada"}, 403

        rota = Rota.query.filter_by(id=rota_id).first()
        if not rota:
            return {"error": "Rota não encontrada"}, 404

        pontos = data.get("pontos", [])
        if not pontos or not isinstance(pontos, list):
            return {"error": "A rota deve conter pelo menos um ponto válido"}, 400

        ultimo_ponto = RotaPonto.query.filter_by(rota_id=rota.id).order_by(RotaPonto.ordem.desc()).first()
        ordem_counter = (ultimo_ponto.ordem + 1) if ultimo_ponto else 1

        for p in pontos:
            nome_p = p.get("nome")
            lat = p.get("latitude")
            lon = p.get("longitude")

            if not nome_p or lat is None or lon is None:
                continue
            
            ponto = Ponto(
                apelido=nome_p,
                latitude=lat,
                longitude=lon
            )
            db.session.add(ponto)
            db.session.flush()

            novo_rota_ponto = RotaPonto(
                rota_id=rota.id,
                ponto_id=ponto.id,
                ordem=ordem_counter
            )
            db.session.add(novo_rota_ponto)
            ordem_counter += 1

        db.session.commit()

        return ({"message": "Pontos adicionados à rota com sucesso"}, 200)