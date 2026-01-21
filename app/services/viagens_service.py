from datetime import datetime
from app.models.viagem import Viagem, ViagemPonto, AlunosConfirmados
from app.models.rota import DiasOperacao, Rota, HorarioRota, RotaPonto, RotaAluno
from app.models.user import User, Aluno
from app.models.base import db
from app.models.enum import StatusViagem, SentidoViagem

class ViagensService:
    
    @staticmethod
    def _get_dia_semana_enum(data_obj):
        """Converte data (0=SEG) para Enum (SEG, TER...)"""
        dias_map = {0: 'SEG', 1: 'TER', 2: 'QUA', 3: 'QUI', 4: 'SEX', 5: 'SAB', 6: 'DOM'}
        return dias_map.get(data_obj.weekday())
    
    @staticmethod
    def _popular_dados_da_viagem(viagem_obj, rota_obj, horario_obj):
        """
        Função Auxiliar que copia os Alunos e Pontos da Rota para a Viagem.
        """
        inscricoes = RotaAluno.query.filter_by(rota_id=rota_obj.id).all()
        
        for inscricao in inscricoes:
            aluno = db.session.get(Aluno, inscricao.aluno_id)
            if not aluno: continue

            p_embarque = None
            p_destino = None
            
            if horario_obj.sentido == SentidoViagem.IDA:
                p_embarque = aluno.ponto_casa_id
                p_destino = aluno.instituicao.ponto_id if aluno.instituicao else None
            
            elif horario_obj.sentido == SentidoViagem.VOLTA:
                p_embarque = aluno.instituicao.ponto_id if aluno.instituicao else None
                p_destino = aluno.ponto_casa_id

            conf = AlunosConfirmados(
                viagem_id=viagem_obj.id, 
                aluno_id=aluno.usuario_id, 
                confirmacao=False,
                ponto_embarque_id=p_embarque,
                ponto_destino_id=p_destino
            )
            db.session.add(conf)

        pontos_rota = RotaPonto.query.filter_by(rota_id=rota_obj.id).order_by(RotaPonto.ordem).all()
        
        ordem_real = 1
        for pr in pontos_rota:
            vp = ViagemPonto(
                viagem_id=viagem_obj.id, 
                ponto_id=pr.ponto_id, 
                ordem=ordem_real, 
                visitado=False
            )
            db.session.add(vp)
            ordem_real += 1
    
    @staticmethod
    def gerar_viagem(user_id, data_input):
        """Gera UMA viagem para UMA rota específica (Modo Manual)"""
        user = db.session.get(User, user_id)
        if not user or str(user.role) not in ['GESTOR', 'MOTORISTA']:
            return {"error": "Permissão negada"}, 403

        rota_id = data_input.get('rota_id')
        data_str = data_input.get('data') 
        
        rota = db.session.get(Rota, rota_id)
        if not rota: return {"error": "Rota não encontrada"}, 404
        
        if rota.prefeitura_id != user.prefeitura_id:
            return {"error": "Acesso negado"}, 403

        try:
            data_viagem = datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError:
            return {"error": "Data inválida. Use YYYY-MM-DD"}, 400

        dia_semana = ViagensService._get_dia_semana_enum(data_viagem)

        horario_selecionado = (
            db.session.query(HorarioRota)
            .join(DiasOperacao)
            .filter(
                HorarioRota.rota_id == rota.id,
                DiasOperacao.dia == dia_semana
            )
            .first()
        )

        if not horario_selecionado:
            return {"error": f"Esta rota não opera em {dia_semana}"}, 400

        if Viagem.query.filter_by(data=data_viagem, horario_rota_id=horario_selecionado.id).first():
             return {"error": "Viagem já gerada para este dia/horário"}, 409

        nova_viagem = Viagem(
            data=data_viagem,
            horario_rota_id=horario_selecionado.id,
            motorista_id=rota.motorista_padrao_id,
            veiculo_id=rota.veiculo_padrao_id,
            status=StatusViagem.AGENDADA
        )
        db.session.add(nova_viagem)
        db.session.flush()

        ViagensService._popular_dados_da_viagem(nova_viagem, rota, horario_selecionado)

        db.session.commit()
        
        return {
            "message": "Viagem gerada com sucesso",
            "id": str(nova_viagem.id),
            "dia": dia_semana
        }, 201

    @staticmethod
    def gerar_viagens_em_lote(user_id, data_str):
        """
        Gera viagens para TODAS as rotas da prefeitura em uma data específica.
        """
        user = db.session.get(User, user_id)
        if not user or str(user.role) != 'GESTOR':
            return {"error": "Permissão negada. Apenas gestores podem gerar lote."}, 403

        try:
            data_viagem = datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError:
            return {"error": "Data inválida. Use YYYY-MM-DD"}, 400

        dia_semana = ViagensService._get_dia_semana_enum(data_viagem)

        rotas = Rota.query.filter_by(prefeitura_id=user.prefeitura_id).all()
        
        relatorio = {
            "total_rotas_analisadas": len(rotas),
            "viagens_criadas": 0,
            "detalhes": []
        }

        for rota in rotas:
            horarios_validos = (
                db.session.query(HorarioRota)
                .join(DiasOperacao)
                .filter(
                    HorarioRota.rota_id == rota.id,
                    DiasOperacao.dia == dia_semana
                )
                .all()
            )

            if not horarios_validos:
                continue 

            for horario in horarios_validos:
                if Viagem.query.filter_by(data=data_viagem, horario_rota_id=horario.id).first():
                    continue 

                # CORREÇÃO: Removido 'rota_id' aqui também
                nova_viagem = Viagem(
                    data=data_viagem,
                    horario_rota_id=horario.id,
                    motorista_id=rota.motorista_padrao_id,
                    veiculo_id=rota.veiculo_padrao_id,
                    status=StatusViagem.AGENDADA
                )
                db.session.add(nova_viagem)
                db.session.flush()

                ViagensService._popular_dados_da_viagem(nova_viagem, rota, horario)

                relatorio["viagens_criadas"] += 1
                relatorio["detalhes"].append(f"Viagem criada: {rota.nome} - {horario.horario_saida}")

        db.session.commit()
        return relatorio, 201

    @staticmethod
    def list_viagens_motorista(user_id):
        viagens = Viagem.query.filter_by(motorista_id=user_id).order_by(Viagem.data.desc()).all()
        return viagens, 200

    @staticmethod
    def controlar_viagem(user_id, viagem_id, data):
        """
        Inicia ou Finaliza viagem.
        """
        user = db.session.get(User, user_id)
        viagem = db.session.get(Viagem, viagem_id)
        
        if not viagem: return {"error": "Viagem not found"}, 404
        
        if str(user.role) == 'MOTORISTA' and viagem.motorista_id != str(user.id):
             return {"error": "Esta viagem não pertence a você"}, 403

        acao = data.get('acao')
        if not acao:
            return {"error": "Campo 'acao' obrigatório"}, 400

        if acao == 'INICIAR':
            if viagem.status != StatusViagem.AGENDADA:
                 return {"error": f"Não é possível iniciar viagem com status {viagem.status.name}"}, 400
            viagem.status = StatusViagem.EM_ANDAMENTO
            viagem.inicio_real = datetime.utcnow()
            
        elif acao == 'FINALIZAR':
            if viagem.status != StatusViagem.EM_ANDAMENTO:
                 return {"error": "A viagem precisa estar em andamento para ser finalizada"}, 400
            viagem.status = StatusViagem.FINALIZADA
            viagem.fim_real = datetime.utcnow()
        else:
            return {"error": "Ação inválida. Use INICIAR ou FINALIZAR"}, 400
            
        db.session.commit()
        
        return viagem, 200

    @staticmethod
    def list_viagens_gestor(user_id, filters):
        user = db.session.get(User, user_id)
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