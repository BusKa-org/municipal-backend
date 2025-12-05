from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from
from datetime import datetime

from ...models.base import db
from ...models.user import User
from ...models.rota import Rota
from ...models.viagem import Viagem
from ...models.municipio import Municipio

gestor_bp = Blueprint("gestor", __name__)


@gestor_bp.route("/rotas", methods=["GET"])
@swag_from('../../../../../docs/gestor-listar_rotas.yml')
@jwt_required()
def listar_rotas_gestor():
    """List all routes in the gestor's municipality."""
    identity = get_jwt_identity()
    user = User.query.get(int(identity))

    if not user or not user.is_gestor():
        return jsonify({"error": "Access restricted to gestores"}), 403

    if not user.municipio_id:
        return jsonify({"error": "Gestor não possui município cadastrado"}), 400

    rotas = Rota.query.filter_by(municipio_id=user.municipio_id).all()
    return jsonify([
        {
            "id": r.id,
            "nome": r.nome,
            "motorista_id": r.motorista_id,
            "municipio_id": r.municipio_id,
        } for r in rotas
    ]), 200


@gestor_bp.route("/viagens", methods=["GET"])
@swag_from('../../../../../docs/gestor-listar_viagens.yml')
@jwt_required()
def listar_viagens():
    """
    Lista todas as viagens disponíveis.
    """
    identity = get_jwt_identity()
    user = User.query.get(int(identity))

    if not user or not user.is_gestor():
        return jsonify({"error": "Access restricted to alunos"}), 403

    if not user.municipio_id:
        return jsonify({"error": "Gestor não possui município cadastrado"}), 400

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


@gestor_bp.route("/viagens", methods=["POST"])
@swag_from('../../../../../docs/gestor-criar_viagens.yml')
@jwt_required()
def criar_viagens():
    """
    Permite que um gestor crie uma viagem associada a uma rota e a um motorista.
    """
    data = request.get_json()
    identity = get_jwt_identity()
    user = User.query.get(int(identity))

    if not user or not user.is_gestor():
        return jsonify({"error": "Access restricted to gestores"}), 403

    if not user.municipio_id:
        return jsonify({"error": "Gestor não possui município cadastrado"}), 400

    rota_id = data.get("rota_id")
    motorista_id = data.get("motorista_id")
    data_viagem = data.get("data")
    horario_inicio = data.get("horario_inicio")
    horario_fim = data.get("horario_fim")
    tipo = data.get("tipo")  #TODO: criar um enum ou alguma docs pra definir isso -> tipo == ["IDA" || "VOLTA"]

    if not all([rota_id, motorista_id, data_viagem, horario_inicio, tipo]):
        return jsonify({"error": "Campos obrigatórios ausentes"}), 400

    rota = Rota.query.get(rota_id)
    if not rota or rota.municipio_id != user.municipio_id:
        return jsonify({"error": "Rota inválida ou fora do município do gestor"}), 403

    viagem = Viagem(
        data=datetime.strptime(data_viagem, "%Y-%m-%d").date(),
        horario_inicio=datetime.strptime(horario_inicio, "%H:%M").time(),
        horario_fim=datetime.strptime(horario_fim, "%H:%M").time() if horario_fim else None,
        tipo=tipo,
        rota_id=rota_id,
        motorista_id=motorista_id
    )

    db.session.add(viagem)
    db.session.commit()

    return jsonify({
        "message": "Viagem criada com sucesso",
        "viagem": {
            "id": viagem.id,
            "data": viagem.data.isoformat(),
            "horario_inicio": viagem.horario_inicio.isoformat(),
            "horario_fim": viagem.horario_fim.isoformat() if viagem.horario_fim else None,
            "tipo": viagem.tipo,
            "rota_id": viagem.rota_id,
            "motorista_id": viagem.motorista_id
        }
    }), 201


@gestor_bp.route("/motoristas", methods=["GET"])
@swag_from('../../../../../docs/gestor-listar_motoristas.yml')
@jwt_required()
def listar_motoristas():
    """List all drivers (motoristas) in the gestor's municipality."""
    identity = get_jwt_identity()
    user = User.query.get(int(identity))

    if not user or not user.is_gestor():
        return jsonify({"error": "Access restricted to gestores"}), 403

    motoristas = User.query.filter_by(municipio_id=user.municipio_id, role="motorista").all()
    return jsonify([
        {"id": m.id, "nome": m.nome, "email": m.email}
        for m in motoristas
    ]), 200


@gestor_bp.route("/relatorios", methods=["GET"])
@swag_from('../../../../../docs/gestor-relatorios_rotas.yml')
@jwt_required()
def relatorios_rotas():
    """Return simple report of trips and distances per route."""
    identity = get_jwt_identity()
    user = User.query.get(int(identity))

    if not user or not user.is_gestor():
        return jsonify({"error": "Access restricted to gestores"}), 403

    rotas = Rota.query.filter_by(municipio_id=user.municipio_id).all()
    result = []

    for rota in rotas:
        viagens = Viagem.query.filter_by(rota_id=rota.id).all()
        total_viagens = len(viagens)
        total_completas = sum(1 for v in viagens if v.horario_fim)
        result.append({
            "rota": rota.nome,
            "total_viagens": total_viagens,
            "completas": total_completas,
        })

    return jsonify(result), 200


@gestor_bp.route("/motoristas", methods=["POST"])
@swag_from('../../../../../docs/gestor-criar_motoristas.yml')
@jwt_required()
def criar_motorista():
    """Create a new motorista (driver) for this municipality."""
    identity = get_jwt_identity()
    user = User.query.get(int(identity))

    if not user or not user.is_gestor():
        return jsonify({"error": "Access restricted to gestores"}), 403

    data = request.get_json()
    nome = data.get("nome").strip()
    email = data.get("email").strip()
    password = data.get("password").strip()

    if not all([nome, email, password]):
        return jsonify({"error": "Nome, email e senha são obrigatórios"}), 400

    from werkzeug.security import generate_password_hash
    hashed_pw = generate_password_hash(password)

    motorista = User(
        nome=nome,
        email=email.lower(),
        senha_hash=hashed_pw,
        role="motorista",
        municipio_id=user.municipio_id,     # TODO: confirmar regra de negocio -> perceba que o gestor cria motoristas somente do mesmo municipio
    )

    db.session.add(motorista)
    db.session.commit()

    return jsonify({"message": "Motorista criado com sucesso."}), 201
