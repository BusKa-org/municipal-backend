from datetime import datetime
from flask import request
from app.models.user import User, Aluno
from app.models.geo import Ponto
from app.models.rota import Rota, RotaAluno, RotaPonto, HorarioRota, DiasOperacao
from app.models.base import db
from app.models.enum import SentidoViagem, DiaDaSemana, UserRole

class RotasService:
    
    @staticmethod
    def list_all_rotas(user_id):
        user = User.query.get(user_id)
        if not user:
            return {"error": "User nao existe"}, 403

        rotas = Rota.query.filter_by(prefeitura_id=user.prefeitura_id).all()

        return ([
            {
                "id": str(r.id), 
                "nome": r.nome, 
                "motorista_id": str(r.motorista_padrao_id) if r.motorista_padrao_id else None
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
            rotas = Rota.query.filter_by(prefeitura_id=user.prefeitura_id).all()

        return ([
            {
                "id": str(r.id), 
                "nome": r.nome, 
                "motorista_id": str(r.motorista_padrao_id) if r.motorista_padrao_id else None
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
            
        if rota.prefeitura_id != user.prefeitura_id:
             return {"error": "Acesso negado a esta rota"}, 403
    
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
        user = db.session.get(User, gestor_id)
        if not user or str(user.role) not in ['GESTOR', 'MOTORISTA']:
            return {"error": "Permissão negada"}, 403

        nome = data.get("nome")
        if not nome:
            return {"error": "Nome da rota é obrigatório"}, 400

        rota = Rota(
            nome=nome,
            motorista_padrao_id=data.get("motorista_padrao_id"),
            veiculo_padrao_id=data.get("veiculo_padrao_id"),
            prefeitura_id=user.prefeitura_id
        )

        db.session.add(rota)
        db.session.flush() 

        if 'pontos' in data:
            for p_data in data['pontos']:
                if 'latitude' not in p_data or 'longitude' not in p_data: 
                    continue
                novo_ponto = Ponto(
                    prefeitura_id=user.prefeitura_id,
                    latitude=p_data['latitude'],
                    longitude=p_data['longitude'],
                    apelido=p_data.get('apelido', f"Ponto {p_data.get('ordem')}")
                )
                db.session.add(novo_ponto)
                db.session.flush()

                rota_ponto = RotaPonto(
                    rota_id=rota.id,
                    ponto_id=novo_ponto.id,
                    ordem=p_data.get('ordem', 0)
                )
                db.session.add(rota_ponto)

        if 'horarios' in data:
            for h_data in data['horarios']:
                novo_horario = HorarioRota(
                    rota_id=rota.id,
                    horario_saida=h_data['horario_saida'],
                    sentido=h_data['sentido']
                )
                db.session.add(novo_horario)
                db.session.flush()

                dias_list = h_data.get('dias', [])
                for dia_str in dias_list:
                    if dia_str in ['SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB', 'DOM']:
                        novo_dia = DiasOperacao(
                            horario_rota_id=novo_horario.id,
                            dia=dia_str
                        )
                        db.session.add(novo_dia)

        try:
            db.session.commit()
            return {"message": "Rota criada com sucesso", "id": str(rota.id)}, 201
        except Exception as e:
            db.session.rollback()
            return {"error": f"Erro ao criar rota: {str(e)}"}, 500

    @staticmethod
    def add_ponto(gestor_id, rota_id, data):
        user = User.query.get(gestor_id)
        
        if not user or str(user.role) not in ['GESTOR', 'MOTORISTA']:
            return {"error": "Permissão negada"}, 403

        rota = Rota.query.get(rota_id)
        if not rota:
            return {"error": "Rota não encontrada"}, 404
            
        if rota.prefeitura_id != user.prefeitura_id:
             return {"error": "Acesso negado"}, 403

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

    @staticmethod
    def add_horario(gestor_id, rota_id, data):
        user = User.query.get(gestor_id)
        if not user or str(user.role) != 'GESTOR':
            return {"error": "Apenas gestores gerenciam horários"}, 403

        rota = Rota.query.get(rota_id)
        if not rota:
            return {"error": "Rota não encontrada"}, 404
        
        if rota.prefeitura_id != user.prefeitura_id:
            return {"error": "Acesso negado"}, 403

        horario_saida = data.get("horario_saida")
        sentido_str = data.get("sentido")
        dias_list = data.get("dias", [])

        if not dias_list:
            return {"error": "Selecione pelo menos um dia da semana"}, 400

        novo_horario = HorarioRota(
            rota_id=rota.id,
            horario_saida=horario_saida,
            sentido=SentidoViagem(sentido_str)
        )
        db.session.add(novo_horario)
        db.session.flush()

        for dia_str in dias_list:
            novo_dia = DiasOperacao(
                horario_rota_id=novo_horario.id,
                dia=DiaDaSemana(dia_str)
            )
            db.session.add(novo_dia)

        db.session.commit()
        return novo_horario, 201

    @staticmethod
    def get_horarios(user_id, rota_id):
        user = User.query.get(user_id)
        rota = Rota.query.get(rota_id)
        if not rota: return {"error": "Rota 404"}, 404
        
        if str(user.role) in ['GESTOR', 'MOTORISTA'] and rota.prefeitura_id != user.prefeitura_id:
            return {"error": "Forbidden"}, 403
            
        return rota.grade_horarios, 200
    
    @staticmethod
    def get_by_id(user_id, rota_id):
        """Busca detalhes de uma rota específica"""
        user = User.query.get(user_id)
        rota = Rota.query.get(rota_id)

        if not rota:
            return {"error": "Rota não encontrada"}, 404

        # Segurança Multi-tenant
        if str(user.role) in ['GESTOR', 'MOTORISTA'] and rota.prefeitura_id != user.prefeitura_id:
            return {"error": "Acesso negado"}, 403

        return {
            "id": str(rota.id),
            "nome": rota.nome,
            "motorista_id": str(rota.motorista_padrao_id) if rota.motorista_padrao_id else None,
            "veiculo_id": str(rota.veiculo_padrao_id) if rota.veiculo_padrao_id else None,
            "prefeitura_id": str(rota.prefeitura_id)
        }, 200

    @staticmethod
    def update_rota(user_id, rota_id, data):
        """Atualiza nome, motorista ou veículo da rota"""
        user = User.query.get(user_id)
        
        # Apenas Gestor edita
        if not user or str(user.role) != 'GESTOR':
            return {"error": "Permissão negada"}, 403

        rota = Rota.query.get(rota_id)
        if not rota:
            return {"error": "Rota não encontrada"}, 404

        # Garante que não está editando rota de outra prefeitura
        if rota.prefeitura_id != user.prefeitura_id:
            return {"error": "Acesso negado"}, 403

        # Atualização dos campos
        if "nome" in data:
            rota.nome = data.get("nome")
        
        if "motorista_id" in data:
            rota.motorista_padrao_id = data.get("motorista_id")
            
        if "veiculo_id" in data:
            rota.veiculo_padrao_id = data.get("veiculo_id")

        db.session.commit()
        
        return {"message": "Rota atualizada com sucesso"}, 200

    @staticmethod
    def delete_rota(user_id, rota_id):
        """Remove a rota"""
        user = User.query.get(user_id)
        
        if not user or str(user.role) != 'GESTOR':
            return {"error": "Permissão negada"}, 403

        rota = Rota.query.get(rota_id)
        if not rota:
            return {"error": "Rota não encontrada"}, 404

        if rota.prefeitura_id != user.prefeitura_id:
            return {"error": "Acesso negado"}, 403

        db.session.delete(rota)
        db.session.commit()

        return {"message": "Rota removida com sucesso"}, 200
    
    @staticmethod
    def listar_rotas_para_aluno(aluno_id):
        """
        Lista rotas da prefeitura do aluno e indica se ele está inscrito.
        """
        aluno = Aluno.query.get(aluno_id)
        if not aluno: return {"error": "Aluno não encontrado"}, 404
        
        rotas = Rota.query.filter_by(prefeitura_id=aluno.prefeitura_id).all()
        
        resultado = []
        for r in rotas:
            inscricao = RotaAluno.query.filter_by(
                rota_id=r.id, 
                aluno_id=aluno.usuario_id
            ).first()

            resultado.append({
                "id": str(r.id),
                "nome": r.nome,
                "inscrito": inscricao is not None,
                "data_inscricao": str(inscricao.data_inscricao) if inscricao else None
            })
            
        return resultado, 200

    @staticmethod
    def inscrever_aluno(aluno_id, rota_id):
        """Cria o registro na tabela RotaAluno"""
        aluno = Aluno.query.get(aluno_id)
        rota = Rota.query.get(rota_id)
        
        if not aluno or not rota: return {"error": "Dados inválidos"}, 404
        
        if aluno.prefeitura_id != rota.prefeitura_id:
            return {"error": "Rota pertence a outra prefeitura"}, 403

        existe = RotaAluno.query.filter_by(rota_id=rota.id, aluno_id=aluno.usuario_id).first()
        if existe:
            return {"message": "Aluno já inscrito nesta rota"}, 200

        nova_inscricao = RotaAluno(
            rota_id=rota.id,
            aluno_id=aluno.usuario_id
        )
        
        db.session.add(nova_inscricao)
        db.session.commit()
        
        return {"message": "Inscrição realizada com sucesso"}, 201

    @staticmethod
    def sair_da_rota(aluno_id, rota_id):
        """Remove o registro da tabela RotaAluno"""
        inscricao = RotaAluno.query.filter_by(rota_id=rota_id, aluno_id=aluno_id).first()
        
        if inscricao:
            db.session.delete(inscricao)
            db.session.commit()
            return {"message": "Removido da rota com sucesso"}, 200
        
        return {"error": "Inscrição não encontrada"}, 404