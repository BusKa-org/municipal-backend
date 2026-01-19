from werkzeug.security import generate_password_hash
from app.models.user import User, Aluno
from app.models.geo import Ponto, Endereco, Instituicao
from app.models.base import db
from app.models.enum import UserRole

class AlunoService:
    
    @staticmethod
    def auto_cadastro(data):
        """
        Aluno se cadastra sozinho.
        A prefeitura é inferida através da Instituição escolhida.
        """
        inst_id = data.get('instituicao_id')
        instituicao = Instituicao.query.get(inst_id)
        if not instituicao:
            return {"error": "Instituição inválida"}, 404
        
        prefeitura_id = instituicao.ponto.prefeitura_id

        if User.query.filter((User.email == data.get('email')) | (User.cpf == data.get('cpf'))).first():
            return {"error": "Email ou CPF já cadastrado"}, 400

        try:
            end_data = data.get('endereco_casa')
            ponto_casa = Ponto(
                prefeitura_id=prefeitura_id,
                latitude=end_data.get('latitude'),
                longitude=end_data.get('longitude'),
                apelido=f"Casa: {data.get('nome')}"
            )
            db.session.add(ponto_casa)
            db.session.flush()

            novo_end = Endereco(
                logradouro=end_data.get('logradouro'),
                numero=end_data.get('numero'),
                bairro=end_data.get('bairro'),
                cidade=end_data.get('cidade'),
                cep=end_data.get('cep'),
                ponto_id=ponto_casa.id
            )
            db.session.add(novo_end)

            novo_aluno = Aluno(
                prefeitura_id=prefeitura_id,
                nome=data.get('nome'),
                email=data.get('email'),
                senha_hash=generate_password_hash(data.get('password')),
                cpf=data.get('cpf'),
                telefone=data.get('telefone'),
                role=UserRole.ALUNO,
                
                matricula=data.get('matricula'),
                instituicao_id=instituicao.id,
                ponto_casa_id=ponto_casa.id,
                nome_pai=data.get('nome_pai'),
                cpf_pai=data.get('cpf_pai'),
                nome_mae=data.get('nome_mae'),
                cpf_mae=data.get('cpf_mae')
            )
            
            db.session.add(novo_aluno)
            db.session.commit()
            
            return novo_aluno, 201

        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    @staticmethod
    def update_me(user_id, data):
        aluno = Aluno.query.get(user_id)
        if not aluno: 
            return {"error": "Aluno não encontrado"}, 404

        try:
            if 'nome' in data: aluno.nome = data['nome']
            if 'telefone' in data: aluno.telefone = data['telefone']

            if 'matricula' in data: aluno.matricula = data['matricula']
            if 'nome_pai' in data: aluno.nome_pai = data['nome_pai']
            if 'cpf_pai' in data: aluno.cpf_pai = data['cpf_pai']
            if 'nome_mae' in data: aluno.nome_mae = data['nome_mae']
            if 'cpf_mae' in data: aluno.cpf_mae = data['cpf_mae']

            if 'endereco_casa' in data:
                end_data = data['endereco_casa']
                
                if aluno.ponto_casa:
                    aluno.ponto_casa.latitude = end_data.get('latitude')
                    aluno.ponto_casa.longitude = end_data.get('longitude')
                    if 'nome' in data:
                        aluno.ponto_casa.apelido = f"Casa: {data['nome']}"
                
                    endereco_bd = Endereco.query.filter_by(ponto_id=aluno.ponto_casa_id).first()
                    
                    if endereco_bd:
                        endereco_bd.logradouro = end_data.get('logradouro')
                        endereco_bd.numero = end_data.get('numero')
                        endereco_bd.bairro = end_data.get('bairro')
                        endereco_bd.cidade = end_data.get('cidade')
                        endereco_bd.cep = end_data.get('cep')
                    else:
                        novo_end = Endereco(
                            ponto_id=aluno.ponto_casa_id,
                            logradouro=end_data.get('logradouro'),
                            numero=end_data.get('numero'),
                            bairro=end_data.get('bairro'),
                            cidade=end_data.get('cidade'),
                            cep=end_data.get('cep')
                        )
                        db.session.add(novo_end)

            db.session.commit()
            return aluno, 200

        except Exception as e:
            db.session.rollback()
            return {"error": "Erro ao atualizar perfil", "details": str(e)}, 500

    @staticmethod
    def delete_me(user_id):
        """Aluno se auto-exclui"""
        aluno = Aluno.query.get(user_id)
        if not aluno: return {"error": "Aluno não encontrado"}, 404

        if aluno.ponto_casa:
            db.session.delete(aluno.ponto_casa)
        
        db.session.delete(aluno)
        db.session.commit()
        
        return {"message": "Conta excluída com sucesso"}, 200

    @staticmethod
    def list_alunos_gestor(gestor_id):
        # Apenas para o gestor ver quem se cadastrou
        gestor = User.query.get(gestor_id)
        if gestor.role != UserRole.GESTOR: return {"error": "Proibido"}, 403
        
        return Aluno.query.filter_by(prefeitura_id=gestor.prefeitura_id).all(), 200