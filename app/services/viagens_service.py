from datetime import datetime
from app.models.viagem import Viagem, ViagemPonto, AlunosConfirmados
from app.models.rota import Rota, HorarioRota, RotaPonto, RotaAluno
from app.models.user import User, Aluno
from app.models.base import db
from app.models.enum import StatusViagem, SentidoViagem

class ViagensService:
    
    @staticmethod
    def gerar_viagem(user_id, data_input):
        """
        Gera uma viagem combinando:
        1. Pontos fixos da Rota (Bairros)
        2. Pontos dinâmicos das Instituições (baseado nos alunos inscritos)
        """
        user = User.query.get(user_id)
        if not user or str(user.role) not in ['GESTOR', 'MOTORISTA']:
            return {"error": "Permissão negada"}, 403

        rota_id = data_input.get('rota_id')
        data_str = data_input.get('data') 
        
        rota = Rota.query.get(rota_id)
        if not rota: return {"error": "Rota não encontrada"}, 404
        
        if rota.prefeitura_id != user.prefeitura_id:
            return {"error": "Acesso negado"}, 403

        if 'horario_id' in data_input:
            horario = HorarioRota.query.get(data_input['horario_id'])
        else:
            horario = rota.grade_horarios[0] if rota.grade_horarios else None

        if not horario:
            return {"error": "Rota sem horários"}, 400

        nova_viagem = Viagem(
            data=data_str,
            horario_rota_id=horario.id,
            motorista_id=rota.motorista_padrao_id,
            veiculo_id=rota.veiculo_padrao_id,
            status=StatusViagem.AGENDADA
        )
        db.session.add(nova_viagem)
        db.session.flush()

        inscricoes = RotaAluno.query.filter_by(rota_id=rota.id).all()
        
        alunos_na_viagem = []
        pontos_instituicoes = set()
        
        for inscricao in inscricoes:
            aluno = Aluno.query.get(inscricao.aluno_id)
            if aluno:
                alunos_na_viagem.append(aluno)
                if aluno.instituicao and aluno.instituicao.ponto_id:
                    pontos_instituicoes.add(aluno.instituicao.ponto_id)


        pontos_fixos_objs = RotaPonto.query.filter_by(rota_id=rota.id).order_by(RotaPonto.ordem.asc()).all()
        ids_pontos_fixos = [p.ponto_id for p in pontos_fixos_objs]

        lista_final_pontos = []

        if horario.sentido == SentidoViagem.IDA:
            
            lista_final_pontos.extend(ids_pontos_fixos)
            
            for p_inst_id in pontos_instituicoes:
                if p_inst_id not in ids_pontos_fixos:
                    lista_final_pontos.append(p_inst_id)
                    
        elif horario.sentido == SentidoViagem.VOLTA:

            for p_inst_id in pontos_instituicoes:
                if p_inst_id not in ids_pontos_fixos:
                    lista_final_pontos.append(p_inst_id)
            
            lista_final_pontos.extend(reversed(ids_pontos_fixos))
            
        else:
            lista_final_pontos.extend(ids_pontos_fixos)

        ordem = 1
        for p_id in lista_final_pontos:
            vp = ViagemPonto(
                viagem_id=nova_viagem.id,
                ponto_id=p_id,
                ordem=ordem,
                visitado=False
            )
            db.session.add(vp)
            ordem += 1

        count_alunos = 0
        for aluno in alunos_na_viagem:
            p_embarque = None
            p_destino = None

            if horario.sentido == SentidoViagem.IDA:
                p_embarque = aluno.ponto_casa_id
                p_destino = aluno.instituicao.ponto_id if aluno.instituicao else None
            elif horario.sentido == SentidoViagem.VOLTA:
                p_embarque = aluno.instituicao.ponto_id if aluno.instituicao else None
                p_destino = aluno.ponto_casa_id

            confirmado = AlunosConfirmados(
                viagem_id=nova_viagem.id,
                aluno_id=aluno.usuario_id,
                confirmacao=False, 
                ponto_embarque_id=p_embarque,
                ponto_destino_id=p_destino
            )
            db.session.add(confirmado)
            count_alunos += 1

        db.session.commit()
        
        return {
            "message": "Viagem gerada com sucesso",
            "id": str(nova_viagem.id),
            "sentido": str(horario.sentido.name),
            "pontos_count": len(lista_final_pontos),
            "alunos_agendados": count_alunos
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

        # Validação de Permissão
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
            return {"error": "Permissão negada"}, 403
        
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