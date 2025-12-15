from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from ...models.base import db
from ...models.user import User
from ...models.rota import Rota, RotaAluno, Ponto
from ...models.viagem import Viagem, Presenca
from ...models.municipio import Municipio
from sqlalchemy import func

aluno_bp = Blueprint("aluno", __name__)

# Rotas ---------------------------------------------------------
@aluno_bp.route("/rotas", methods=["GET"])
@swag_from('../../../../../docs/aluno-listar_rotas.yml')
@jwt_required()
def listar_rotas():
    """
    Lista todas as rotas disponíveis no município do aluno.
    """
    identity = get_jwt_identity()
    user = User.query.get(int(identity))

    if not user or not user.is_aluno():
        return jsonify({"error": "Access restricted to alunos"}), 403

    if not user.municipio_id:
        return jsonify({"error": "Aluno não possui município cadastrado"}), 400

    rotas = (
        db.session.query(Rota)
        .join(Municipio, Rota.municipio_id == Municipio.id)
        .filter(Rota.municipio_id == user.municipio_id)
        .all()
    )

    return jsonify([
        {
            "id": r.id,
            "nome": r.nome,
            "motorista_id": r.motorista_id,
            "municipio_id": r.municipio_id,
            "municipio_nome": r.municipio.nome if r.municipio else None
        } for r in rotas
    ]), 200

@aluno_bp.route("/me/rotas", methods=["GET"])
@swag_from('../../../../../docs/aluno-listar_rotas_inscritas.yml')
@jwt_required()
def listar_rotas_aluno():
    """
    Lista todas as rotas nas quais o aluno está inscrito.
    """
    identity = get_jwt_identity()
    user = User.query.get(int(identity))

    if not user or not user.is_aluno():
        return jsonify({"error": "Access restricted to alunos"}), 403

    inscricoes = (
        db.session.query(Rota)
        .join(RotaAluno, Rota.id == RotaAluno.rota_id)
        .join(Municipio, Rota.municipio_id == Municipio.id)
        .filter(RotaAluno.aluno_id == user.id)
        .all()
    )

    return jsonify([
        {
            "id": r.id,
            "nome": r.nome,
            "motorista_id": r.motorista_id,
            "municipio_id": r.municipio_id,
            "municipio_nome": r.municipio.nome if r.municipio else None
        } for r in inscricoes
    ]), 200


@aluno_bp.route("/rotas/<int:rota_id>/pontos", methods=["GET"])
@jwt_required()
def listar_pontos_rota(rota_id):
    """
    Lista todos os pontos de uma rota na qual o aluno está inscrito.
    """
    identity = get_jwt_identity()
    user = User.query.get(int(identity))

    if not user or not user.is_aluno():
        return jsonify({"error": "Access restricted to alunos"}), 403

    # Verificar se o aluno está inscrito na rota
    inscricao = RotaAluno.query.filter_by(aluno_id=user.id, rota_id=rota_id).first()
    if not inscricao:
        return jsonify({"error": "Aluno não está inscrito nesta rota"}), 403

    rota = Rota.query.get(rota_id)
    if not rota:
        return jsonify({"error": "Rota não encontrada"}), 404

    pontos = Ponto.query.filter_by(rota_id=rota_id).all()
    
    # Extrair latitude e longitude da geometria POINT
    pontos_data = []
    for ponto in pontos:
        # A localizacao é uma Geometry POINT, precisamos extrair lat/lon
        # Usando ST_X e ST_Y do PostGIS
        lon = db.session.scalar(func.ST_X(ponto.localizacao))
        lat = db.session.scalar(func.ST_Y(ponto.localizacao))
        
        # Determinar o tipo do ponto (primeiro = origem, último = destino, outros = paradas)
        pontos_data.append({
            "id": ponto.id,
            "nome": ponto.nome,
            "latitude": float(lat) if lat is not None else None,
            "longitude": float(lon) if lon is not None else None,
        })
    
    # Marcar o primeiro ponto como origem e o último como destino
    if pontos_data:
        pontos_data[0]["tipo"] = "origem"
        if len(pontos_data) > 1:
            pontos_data[-1]["tipo"] = "destino"
            # Marcar os pontos intermediários como paradas
            for i in range(1, len(pontos_data) - 1):
                pontos_data[i]["tipo"] = "parada"
    
    return jsonify(pontos_data), 200

@aluno_bp.route("/rotas/<int:rota_id>/inscricao", methods=["PUT"])
@swag_from('../../../../../docs/aluno-inscricao_rota.yml')
@jwt_required()
def gerenciar_inscricao_rota(rota_id):
    """
    Permite que o aluno se inscreva ou cancele a inscrição em uma rota.
    """
    identity = get_jwt_identity()
    user = User.query.get(int(identity))

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


# Viagens -------------------------------------------------------
@aluno_bp.route("/viagens", methods=["GET"])
@swag_from('../../../../../docs/aluno-listar_viagens.yml')
@jwt_required()
def listar_viagens():
    """
    Lista todas as viagens disponíveis no município do aluno.
    """
    identity = get_jwt_identity()
    user = User.query.get(int(identity))

    if not user or not user.is_aluno():
        return jsonify({"error": "Access restricted to alunos"}), 403

    if not user.municipio_id:
        return jsonify({"error": "Aluno não possui município cadastrado"}), 400

    viagens = (
        db.session.query(Viagem)
        .join(Rota, Viagem.rota_id == Rota.id)
        .filter(Rota.municipio_id == user.municipio_id)
        .all()
    )

    return jsonify([
        {
            "id": v.id,
            "data": v.data.isoformat(),
            "horario_inicio": v.horario_inicio.isoformat() if v.horario_inicio else None,
            "horario_fim": v.horario_fim.isoformat() if v.horario_fim else None,
            "tipo": v.tipo,
            "rota_id": v.rota_id,
            "motorista_id": v.motorista_id
        } for v in viagens
    ]), 200

@aluno_bp.route("/viagens/<int:viagem_id>/presenca", methods=["GET"])
@jwt_required()
def obter_presenca_viagem(viagem_id):
    """
    Obtém o status de presença do aluno em uma viagem.
    """
    identity = get_jwt_identity()
    user = User.query.get(int(identity))

    if not user or not user.is_aluno():
        return jsonify({"error": "Access restricted to alunos"}), 403

    viagem = Viagem.query.get(viagem_id)
    if not viagem:
        return jsonify({"error": "Viagem não encontrada"}), 404

    presenca = Presenca.query.filter_by(aluno_id=user.id, viagem_id=viagem.id).first()

    if not presenca:
        return jsonify({
            "presente": False,
            "confirmada": False,
            "cancelada": False
        }), 200

    return jsonify({
        "presente": presenca.confirmada and not presenca.cancelada,
        "confirmada": presenca.confirmada,
        "cancelada": presenca.cancelada
    }), 200

@aluno_bp.route("/viagens/<int:viagem_id>/presenca", methods=["PUT"])
@swag_from('../../../../../docs/aluno-presenca_viagem.yml')
@jwt_required()
def alterar_presenca_viagem(viagem_id):
    """
    Permite que o aluno confirme ou cancele sua presença em uma viagem.
    """
    identity = get_jwt_identity()
    user = User.query.get(int(identity))

    if not user or not user.is_aluno():
        return jsonify({"error": "Access restricted to alunos"}), 403

    viagem = Viagem.query.get(viagem_id)
    if not viagem:
        return jsonify({"error": "Viagem não encontrada"}), 404

    data = request.get_json()
    presente = data.get("presente")

    if presente not in [True, False]:
        return jsonify({"error": "Campo 'presente' deve ser True ou False."}), 400

    presenca = Presenca.query.filter_by(aluno_id=user.id, viagem_id=viagem.id).first()

    if not presenca:
        presenca = Presenca(
            aluno_id=user.id,
            viagem_id=viagem.id,
            confirmada=presente,
            cancelada=not presente
        )
        db.session.add(presenca)
    else:
        presenca.confirmada = presente
        presenca.cancelada = not presente

    db.session.commit()
    estado = "confirmada" if presente else "cancelada"
    return jsonify({"message": f"Presença {estado} com sucesso."}), 200

@aluno_bp.route("/me/viagens", methods=["GET"])
@swag_from('../../../../../docs/aluno-listar_viagens_inscritas.yml')
@jwt_required()
def listar_viagens_aluno():
    """
    Lista todas as viagens nas quais o aluno está registrado (com presença).
    """
    identity = get_jwt_identity()
    user = User.query.get(int(identity))

    if not user or not user.is_aluno():
        return jsonify({"error": "Access restricted to alunos"}), 403

    viagens = (
        db.session.query(Viagem)
        .join(Presenca, Viagem.id == Presenca.viagem_id)
        .filter(Presenca.aluno_id == user.id)
        .all()
    )

    return jsonify([
        {
            "id": v.id,
            "data": v.data.isoformat(),
            "horario_inicio": v.horario_inicio.isoformat() if v.horario_inicio else None,
            "horario_fim": v.horario_fim.isoformat() if v.horario_fim else None,
            "tipo": v.tipo,
            "rota_id": v.rota_id,
            "motorista_id": v.motorista_id,
        } for v in viagens
    ]), 200
