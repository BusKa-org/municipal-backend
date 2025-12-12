from datetime import datetime

from ..models.user import User
from ..models.viagem import Viagem
from ..models.base import db


class ViagensService:
    @staticmethod
    def list_all_viagens(user_id):
        """ Lista todas as viagens daquele municipio """

        user = User.query.get(user_id)

        viagens = Viagem.query.all(municipio_id=user.municipio_id)

        return ([
            {
                "id": v.id,
                "rota_id": v.rota_id,
                "municipio_id": v.municipio_id,
                "motorista_id": v.motorista_id,
                "tipo":v.tipo,
                "horario de inicio": v.horario_inicio.isoformat() if v.horario_inicio else None,
                "previsao horario fim":  v.horario_fim if v.horario_fim else None, }
            for v in viagens
        ], 200)

    @staticmethod
    def list_my_viagens(user_id):
        """ Lista as viagens naquele dia """

        user = User.query.get(user_id)
        if not user:
            return {"error": "User nao existe"}, 403
        if not user.municipio_id:
            return {"error": "user não possui município cadastrado"}, 400

        data_hoje = date.today()
        if user.is_aluno():
            rotas = Viagem.query.join(ViagemAluno).filter(
                    ViagemAluno.aluno_id == user.id,
                    Viagem.data == data_hoje
            ).all()

        elif user.is_motorista():
            rotas = Viagem.query.filter_by(user_id=user.id,data=data_hoje).all()

        elif user.is_gestor():
            rotas = Viagem.query.all(data=data_hoje, municipio_id=user.municipio_id)

        return ([
            {
                "id": v.id,
                "rota_id": v.rota_id,
                "municipio_id": v.municipio_id,
                "motorista_id": v.motorista_id,
                "tipo":v.tipo,
                "horario de inicio": v.horario_inicio.isoformat() if v.horario_inicio else None,
                "previsao horario fim":  v.horario_fim if v.horario_fim else None, }
            for v in viagens
        ], 200)

    @staticmethod
    def presenca_aluno_viagem(aluno_id, viagem_id):
        """
        Permite que o aluno confirme ou cancele sua presença em uma viagem
        """
        user = User.query.get(aluno_id)

        if not user or not user.is_aluno():
            return {"error": "Access restricted to alunos"}, 403

        viagem = Viagem.query.get(viagem_id)
        if not viagem:
            return {"error": "Viagem não encontrada"}, 404
    
        data = request.get_json()
        presente = data.get("presente")
    
        if presente not in [True, False]:
            return {"error": "Campo 'presente' deve ser True ou False."}, 400
    
        presenca = ViagemAluno.query.filter_by(aluno_id=user.id, viagem_id=viagem.id).first()
    
        if not presenca:
            presenca = ViagemAluno(aluno_id=user.id, viagem_id=viagem.id, presenca=presente)
            db.session.add(presenca)
        else:
            presenca.presente = presente
    
        db.session.commit()
        estado = "confirmada" if presente else "cancelada"

        return {"message": f"Presença {estado} com sucesso."}, 200


    @staticmethod
    def start_viagem(rota_id):
        """
        Permite que uma viagem associada a uma rota seja criada.
        """
    
        rota = Rota.query.get(rota_id)
        if not rota or not rota.municipio_id:
            return {"error": "Rota inválida"}, 403
    
        # TODO: do jeito que esta, uma Viagem eh uma rota com mais infos
        #       sendo que uma viagem deveria ser criada AUTOMATICAMENTE a partir de uma viagem 
        #       logo, quem vai adicionar essas 'mais infos' 'a Viagem ? 
        #       Solucoes:
        #           i. Rota e Viagem devem compartilhar os mesmos atributos
        #           ii. Devemos repensar essa logica

        #viagem = Viagem(
        #    data=datetime.strptime(data_viagem, "%Y-%m-%d").date(),
        #    horario_inicio=datetime.strptime(horario_inicio, "%H:%M").time(),
        #    horario_fim=datetime.strptime(horario_fim, "%H:%M").time() if horario_fim else None,
        #    tipo=tipo,
        #    rota_id=rota_id,
        #    motorista_id=rota.motorista_id,
        #    municipio_id=rota.motorista_id
        #)
        viagem = None
    
        db.session.add(viagem)
        db.session.commit()
    
        return {None}
        #return jsonify({
        #    "message": "Viagem criada com sucesso",
        #    "viagem": {
        #        "id": viagem.id,
        #        "data": viagem.data.isoformat(),
        #        "horario_inicio": viagem.horario_inicio.isoformat(),
        #        "horario_fim": viagem.horario_fim.isoformat() if viagem.horario_fim else None,
        #        "tipo": viagem.tipo,
        #        "rota_id": viagem.rota_id,
        #        "motorista_id": viagem.motorista_id
        #    }
        #}), 201



    @staticmethod
    def start_viagem(motorista_id, viagem_id):
        user = User.query.get(motorista_id)
        if not user or not user.is_motorista():
            return {"error": "Access restricted to motoristas"}, 403

        viagem = Viagem.query.filter_by(id=viagem_id, motorista_id=user.id).first()
        if not viagem:
            return {"error": "Viagem não encontrada"}, 404

        viagem.horario_inicio = datetime.utcnow()
        db.session.commit()

        return {"message": "Viagem iniciada com sucesso"}, 200

    @staticmethod
    def end_viagem(motorista_id, viagem_id):
        user = User.query.get(motorista_id)
        if not user or not user.is_motorista():
            return {"error": "Access restricted to motoristas"}, 403

        viagem = Viagem.query.filter_by(id=viagem_id, motorista_id=user.id).first()
        if not viagem:
            return {"error": "Viagem não encontrada"}, 404

        viagem.horario_fim = datetime.utcnow()
        db.session.commit()

        return {"message": "Viagem finalizada com sucesso"}, 200
