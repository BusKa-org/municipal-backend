from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from
from datetime import datetime
from ...models.base import db
from ...models.user import User
from ...models.rota import Rota, Ponto
from ...models.viagem import Viagem

motorista_bp = Blueprint("motorista", __name__)


# Rota ----------------------------------------------------------
@motorista_bp.route("/rotas", methods=["GET"])
@swag_from('../../../../../docs/motorista-listar_rotas.yml')
@jwt_required()
def listar_rotas_motorista():
    """List all routes assigned to the logged-in driver (motorista)"""
    identity = get_jwt_identity()
    user = User.query.get(int(identity))

    if not user or not user.is_motorista():
        return jsonify({"error": "Access restricted to motoristas"}), 403

    rotas = Rota.query.filter_by(motorista_id=user.id).all()
    return jsonify([
        {
            "id": r.id,
            "nome": r.nome,
            "municipio_id": r.municipio_id
        } for r in rotas
    ]), 200

#TODO:  seria interessante o gestor tambem acessar 'essa rota'
#       creio que cirar um arquivo chamado rotas.py no qual 
#       tanto o motorista quanto o gestor podem acessar
#       ou fazemos isso, ou temos que repetir o mesmo codigo da rota
#       para o gestor e o motorista.
    #       Perceba que fazemos isso com outras rotas tambem, nao so esta. 
    #       Seria interessante atualizar todas.
@motorista_bp.route("/rotas", methods=["POST"])
@swag_from('../../../../../docs/motorista-criar_rota.yml')
@jwt_required()
def criar_rota():
    """
    Permite que um motorista crie uma rota e adicione pontos a ela.
    """
    data = request.get_json()
    identity = get_jwt_identity()
    user = User.query.get(int(identity))

    if not user or not user.is_motorista():
        return jsonify({"error": "Access restricted to motoristas"}), 403

    nome = data.get("nome")
    municipio_id = user.municipio_id

    if not municipio_id:
        return jsonify({"error": "Motorista não tem nenhum munincípio cadastrado"}), 400

    # TODO: isso aqui tem que ser feito no service, nao na parte das rotas
    rota = Rota(
        nome=nome,
        municipio_id=municipio_id,
        motorista_id=user.id
    )

    db.session.add(rota)
    db.session.commit()

    return jsonify({
        "message": "Rota criada com sucesso",
        "rota": {
            "id": rota.id,
            "nome": rota.nome,
            "municipio_id": rota.municipio_id,
            "motorista_id": rota.motorista_id
        }
    }), 201

@motorista_bp.route("/rotas/<int:rota_id>/ponto", methods=["POST"])
@swag_from('../../../../../docs/motorista-adicionar_ponto.yml')
@jwt_required()
def adicionar_ponto(rota_id):
    """
    Permite que um motorista crie uma rota e adicione pontos a ela.
    """
    data = request.get_json()
    identity = get_jwt_identity()
    user = User.query.get(int(identity))

    # TODO: deve existir alguma forma melhor de verificar se os campos da request estao corretos, pesquisar
    if not user or not user.is_motorista():
        return jsonify({"error": "Access restricted to motoristas"}), 403

    municipio_id = data.get("municipio_id")

    if not municipio_id:
        return jsonify({"error": "Motorista não tem nenhum munincípio cadastrado"}), 400

    if not rota_id or not (rota := Rota.query.get(rota_id)):
        return jsonify({"error": "Rota não encontrada"}), 404

    pontos = data.get("pontos", [])  # lista de {nome, latitude, longitude}

    if not pontos or not isinstance(pontos, list):
        return jsonify({"error": "A rota deve conter pelo menos um ponto válido"}), 400

    # TODO: isso aqui tem que ser feito no service, nao na parte das rotas
    for p in pontos:
        nome_ponto = p.get("nome")
        lat = p.get("latitude")
        lon = p.get("longitude")

        if not nome_ponto or lat is None or lon is None:
            continue  

        ponto = Ponto(
            nome=nome_ponto,
            localizacao=f"POINT({lon} {lat})",
            rota_id=rota.id
        )
        db.session.add(ponto)
    db.session.commit()

    return jsonify({
        "message": "Pontos adicionados a rota",
        "rota": {
            "id": rota.id,
            "nome": rota.nome,
            "pontos": [{"nome": p["nome"], "latitude": p["latitude"], "longitude": p["longitude"]} for p in pontos]
        }
    }), 201


# Viagens ----------------------------------------------------------
@motorista_bp.route("/viagens", methods=["GET"])
@swag_from('../../../../../docs/motorista-listar_viagens.yml')
@jwt_required()
def listar_viagens_motorista():
    """List trips (viagens) for the driver's routes"""
    identity = get_jwt_identity()
    user = User.query.get(int(identity))

    if not user or not user.is_motorista():
        return jsonify({"error": "Access restricted to motoristas"}), 403

    viagens = Viagem.query.filter_by(motorista_id=user.id).all()
    return jsonify([
        {
            "id": v.id,
            "data": v.data.isoformat(),
            "horario_inicio": v.horario_inicio.isoformat(),
            "horario_fim": v.horario_fim.isoformat() if v.horario_fim else None,
            "rota_id": v.rota_id,
            "tipo": v.tipo,
        } for v in viagens
    ]), 200


@motorista_bp.route("/viagens/<int:viagem_id>/iniciar", methods=["POST"])
@swag_from('../../../../../docs/motorista-iniciar_viagem.yml')
@jwt_required()
def iniciar_viagem(viagem_id):
    """Mark a trip as started"""
    identity = get_jwt_identity()
    user = User.query.get(int(identity))

    if not user or not user.is_motorista():
        return jsonify({"error": "Access restricted to motoristas"}), 403

    viagem = Viagem.query.filter_by(id=viagem_id, motorista_id=user.id).first()
    if not viagem:
        return jsonify({"error": "Viagem not found"}), 404

    viagem.horario_inicio = datetime.utcnow()
    db.session.commit()

    return jsonify({"message": "Viagem iniciada com sucesso."}), 200


@motorista_bp.route("/viagens/<int:viagem_id>/finalizar", methods=["POST"])
@swag_from('../../../../../docs/motorista-finalizar_viagem.yml')
@jwt_required()
def finalizar_viagem(viagem_id):
    """Mark a trip as finished"""
    identity = get_jwt_identity()
    motorista = User.query.get(int(identity))

    if not user or not user.is_motorista():
        return jsonify({"error": "Access restricted to motoristas"}), 403

    viagem = Viagem.query.filter_by(id=viagem_id, motorista_id=user.id).first()
    if not viagem:
        return jsonify({"error": "Viagem not found"}), 404

    viagem.horario_fim = datetime.utcnow()
    db.session.commit()

    return jsonify({"message": "Viagem finalizada com sucesso."}), 200
