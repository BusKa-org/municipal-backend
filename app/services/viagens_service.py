from datetime import datetime
from app.models.viagem import Viagem, ViagemPonto
from app.models.rota import Rota, HorarioRota, RotaPonto
from app.models.user import User
from app.models.base import db
from app.models.enum import StatusViagem, SentidoViagem

class ViagensService:
    
    @staticmethod
    def gerar_viagem(user_id, data_input):
        """
        Gera uma viagem aplicando a lógica de sentido (IDA/VOLTA).
        """
        user = User.query.get(user_id)
        if not user or str(user.role) not in ['GESTOR', 'MOTORISTA']:
            return {"error": "Permissão negada"}, 403

        rota_id = data_input.get('rota_id')
        data_str = data_input.get('data') # YYYY-MM-DD
        
        rota = Rota.query.get(rota_id)
        if not rota: return {"error": "Rota não encontrada"}, 404
        
        if rota.prefeitura_id != user.prefeitura_id:
            return {"error": "Acesso negado"}, 403

        if 'horario_id' in data_input:
            horario = HorarioRota.query.get(data_input['horario_id'])
        else:
            horario = HorarioRota.query.filter_by(rota_id=rota.id).first()

        if not horario:
            return {"error": "Rota não possui horários ou horário inválido"}, 400

        nova_viagem = Viagem(
            data=data_str,
            horario_rota_id=horario.id,
            motorista_id=rota.motorista_padrao_id,
            veiculo_id=rota.veiculo_padrao_id,
            status=StatusViagem.AGENDADA
        )
        db.session.add(nova_viagem)
        db.session.flush()

        pontos_rota = RotaPonto.query.filter_by(rota_id=rota.id).order_by(RotaPonto.ordem.asc()).all()

        if horario.sentido == SentidoViagem.VOLTA:
            pontos_processados = list(reversed(pontos_rota))
        else:
            pontos_processados = pontos_rota

        ordem_atual = 1
        for rp in pontos_processados:
            vp = ViagemPonto(
                viagem_id=nova_viagem.id,
                ponto_id=rp.ponto_id,
                
                ordem=ordem_atual, 
                
                visitado=False
            )
            db.session.add(vp)
            ordem_atual += 1
        
        db.session.commit()
        
        return {
            "message": "Viagem gerada com sucesso",
            "id": str(nova_viagem.id),
            "sentido": str(horario.sentido.value),
            "pontos_count": len(pontos_processados)
        }, 201

    @staticmethod
    def list_viagens_motorista(user_id):
        viagens = Viagem.query.filter_by(motorista_id=user_id).order_by(Viagem.data.desc()).all()
        return viagens, 200

    @staticmethod
    def controlar_viagem(user_id, viagem_id, data_action):
        viagem = Viagem.query.get(viagem_id)
        if not viagem: return {"error": "Viagem 404"}, 404

        user = User.query.get(user_id)
        if not user: return {"error": "Usuário inválido"}, 403

        is_driver = str(viagem.motorista_id) == str(user.id)

        is_gestor_autorizado = False
        if str(user.role) == 'GESTOR':
            if viagem.horario_rota and viagem.horario_rota.rota:
                 if viagem.horario_rota.rota.prefeitura_id == user.prefeitura_id:
                     is_gestor_autorizado = True
            elif viagem.motorista:
                 if viagem.motorista.prefeitura_id == user.prefeitura_id:
                     is_gestor_autorizado = True
            elif not viagem.horario_rota and not viagem.motorista:
                 is_gestor_autorizado = True

        if not (is_driver or is_gestor_autorizado):
            return {"error": "Permissão negada: Apenas o motorista responsável ou gestor da prefeitura podem alterar esta viagem"}, 403
        
        acao = data_action.get('acao')
        
        if acao == 'INICIAR':
            if viagem.status != StatusViagem.AGENDADA:
                return {"error": "Viagem já iniciada ou finalizada"}, 400
            viagem.status = StatusViagem.EM_ANDAMENTO
            viagem.inicio_real = datetime.utcnow()
            
        elif acao == 'FINALIZAR':
            viagem.status = StatusViagem.FINALIZADA
            viagem.fim_real = datetime.utcnow()
            
        elif acao == 'REGISTRAR_PONTO':
            ponto_id = data_action.get('ponto_id')
            vp = ViagemPonto.query.filter_by(viagem_id=viagem.id, ponto_id=ponto_id).first()
            if vp:
                vp.visitado = True
                vp.chegada_real = datetime.utcnow()
            else:
                return {"error": "Ponto não pertence a esta viagem"}, 400

        db.session.commit()
        return viagem, 200

    @staticmethod
    def list_viagens_gestor(user_id, filters):
        """
        Lista todas as viagens da prefeitura do gestor, com filtros opcionais.
        SEGURANÇA: Faz o Join para garantir que só traga dados da prefeitura correta.
        """
        user = User.query.get(user_id)
        if not user or str(user.role) != 'GESTOR':
            return {"error": "Apenas gestores podem acessar o histórico completo"}, 403

        query = Viagem.query
        query = query.join(HorarioRota).join(Rota)
        query = query.filter(Rota.prefeitura_id == user.prefeitura_id)
        
        if filters.get('data_inicio'):
            query = query.filter(Viagem.data >= filters.get('data_inicio'))
        
        if filters.get('data_fim'):
            query = query.filter(Viagem.data <= filters.get('data_fim'))

        if filters.get('status'):
            query = query.filter(Viagem.status == StatusViagem(filters.get('status')))

        if filters.get('motorista_id'):
            query = query.filter(Viagem.motorista_id == filters.get('motorista_id'))

        if filters.get('rota_id'):
            query = query.filter(Rota.id == filters.get('rota_id'))

        viagens = query.order_by(Viagem.data.desc(), Viagem.horario_rota_id).all()

        return viagens, 200