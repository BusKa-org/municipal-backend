from datetime import datetime

from ..models.user import User
from ..models.rota import Rota, RotaAluno, Ponto
from ..models.base import db


class RotasService:
    @staticmethod
    def list_all_rotas(user_id):
        user = User.query.get(user_id)
        if not user:
            return {"error": "User nao existe"}, 403

        if user.is_aluno():
            return {"error": "Access restricted to motoristas and gestores"}, 403

        rotas = Rota.query.all(municipio_id=user.municipio_id)

        return ([
            {"id": r.id, "nome": r.nome, "municipio_id": r.municipio_id, "motorista_id": r.motorista_id}
            for r in rotas
        ], 200)


    @staticmethod
    def list_my_rotas(user_id):
        user = User.query.get(user_id)
        if not user:
            return {"error": "User nao existe"}, 403
        if not user.municipio_id:
            return jsonify({"error": "user não possui município cadastrado"}), 400

        if user.is_aluno():
            rotas = RotaAluno.query.filter_by(user_id=user.id).all()

        elif user.is_motorista():
            rotas = Rota.query.filter_by(user_id=user.id).all()

        elif user.is_gestor():
            rotas = Rota.query.filter_by(municipio_id=user.municipio_id).all()

        return ([
            {"id": r.id, "nome": r.nome, "municipio_id": r.municipio_id, "motorista_id": r.motorista_id}
            for r in rotas
        ], 200)

    @staticmethod
    def inscricao_aluno_rota(aluno_id, rota_id):
        """
        Permite que o aluno se inscreva ou cancele a inscrição em uma rota.
        """
    
        if not user or not user.is_aluno():
            return jsonify({"error": "Access restricted to alunos"}), 403
    
        rota = Rota.query.get(rota_id)
        if not rota:
            return jsonify({"error": "Rota não encontrada"}), 404
    
        data = request.get_json()
        acao = data.get("acao", "").lower()  # "inscrever" ou "desinscrever"
    
        if acao not in ["inscrever", "desinscrever"]:
            return jsonify({"error": "Ação inválida. Use 'inscrever' ou 'desinscrever'."}), 400
    
        inscricao = RotaAluno.query.filter_by(aluno_id=user.id, rota_id=rota.id).first()
    
        if acao == "inscrever":
            if inscricao:
                return jsonify({"message": "Aluno já inscrito nesta rota."}), 200
            nova_inscricao = RotaAluno(aluno_id=user.id, rota_id=rota.id)
            db.session.add(nova_inscricao)
            db.session.commit()
            return jsonify({"message": "Aluno inscrito na rota com sucesso."}), 200
    
        elif acao == "desinscrever":
            if not inscricao:
                return jsonify({"message": "Aluno não está inscrito nesta rota."}), 200
            db.session.delete(inscricao)
            db.session.commit()
            return jsonify({"message": "Aluno desinscrito da rota com sucesso."}), 200

    @staticmethod
    def create_rota(gestor_id, data):
        user = User.query.get(gestor_id)
        if not user or not user.is_gestor():
            return {"error": "Access restricted to users"}, 403

        nome = data.get("nome")
        if not nome:
            return {"error": "Nome da rota é obrigatório"}, 400

        if not user.municipio_id:
            return {"error": "user não tem município cadastrado"}, 400

        user_m_id = data.get("motorista_id")
        user_m = User.query.get(user_m_id)
        if not user_md or not user_m.is_motorista():
            return {"error": "É necessário escolher um motorista para poder cadastrar a rota"}, 400

        rota = Rota(
            nome=nome,
            municipio_id=user.municipio_id,
            motorista_id=user_m_id,
        )

        db.session.add(rota)
        db.session.commit()

        return ({
            "message": "Rota criada com sucesso",
            "rota": {
                "id": rota.id,
                "nome": rota.nome,
                "municipio_id": rota.municipio_id,
                "motorista_id": rota.motorista_id,
            }
        }, 201)

    @staticmethod
    def add_ponto(gestor_id, rota_id, data):
        user = User.query.get(gestor_id)
        if not user or not user.is_gestor():
            return {"error": "Access restricted to gestor"}, 403

        rota = Rota.query.filter_by(id=rota_id).first()
        if not rota:
            return {"error": "Rota não encontrada"}, 404

        pontos = data.get("pontos", [])
        if not pontos or not isinstance(pontos, list):
            return {"error": "A rota deve conter pelo menos um ponto válido"}, 400

        for p in pontos:
            nome_p = p.get("nome")
            lat = p.get("latitude")
            lon = p.get("longitude")

            if not nome_p or lat is None or lon is None:
                continue

            ponto = Ponto(
                nome=nome_p,
                localizacao=f"POINT({lon} {lat})",
                rota_id=rota.id
            )
            db.session.add(ponto)

        db.session.commit()

        return ({
            "message": "Pontos adicionados à rota",
            "rota": {
                "id": rota.id,
                "nome": rota.nome,
                "pontos": [{"nome": p["nome"], "latitude": p["latitude"], "longitude": p["longitude"]} for p in pontos]
            }
        }, 201)
