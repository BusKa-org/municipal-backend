import logging

from werkzeug.security import generate_password_hash
from app.models.user import User, Aluno
from app.models.geo import Ponto, Endereco, Instituicao
from app.models.base import db
from app.models.enum import UserRole
from app.core.exceptions import AppError, NotFoundError, ValidationError, ForbiddenError

logger = logging.getLogger(__name__)


class AlunoService:
    
    @staticmethod
    def auto_cadastro(data: dict) -> Aluno:
        """
        Aluno se cadastra sozinho.
        A prefeitura é inferida através da Instituição escolhida.
        
        Returns: Aluno object
        Raises: NotFoundError, ValidationError, AppError
        """
        inst_id = data.get('instituicao_id')
        instituicao = Instituicao.query.get(inst_id)
        if not instituicao:
            raise NotFoundError("Instituição inválida")
        
        prefeitura_id = instituicao.ponto.prefeitura_id

        if User.query.filter((User.email == data.get('email')) | (User.cpf == data.get('cpf'))).first():
            raise ValidationError("Email ou CPF já cadastrado")

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
            
            return novo_aluno
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating student: {e}")
            raise AppError(f"Erro ao criar aluno: {str(e)}", 500)

    @staticmethod
    def update_me(user_id: str, data: dict) -> Aluno:
        """
        Atualiza perfil do aluno.
        
        Returns: Aluno object
        Raises: NotFoundError, AppError
        """
        aluno = Aluno.query.get(user_id)
        if not aluno:
            raise NotFoundError("Aluno não encontrado")

        try:
            # Update simple fields
            for field in ('nome', 'telefone', 'matricula', 'nome_pai', 'cpf_pai', 'nome_mae', 'cpf_mae'):
                if field in data:
                    setattr(aluno, field, data[field])

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
            return aluno
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating student profile: {e}")
            raise AppError(f"Erro ao atualizar perfil: {str(e)}", 500)

    @staticmethod
    def delete_me(user_id: str) -> None:
        """
        Aluno se auto-exclui.
        
        Raises: NotFoundError, AppError
        """
        aluno = Aluno.query.get(user_id)
        if not aluno:
            raise NotFoundError("Aluno não encontrado")

        try:
            if aluno.ponto_casa:
                db.session.delete(aluno.ponto_casa)
            
            db.session.delete(aluno)
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting student account: {e}")
            raise AppError(f"Erro ao excluir conta: {str(e)}", 500)

    @staticmethod
    def list_alunos_gestor(gestor_id: str) -> list[Aluno]:
        """
        Lista alunos da prefeitura (apenas para gestores).
        
        Returns: List of Aluno objects
        Raises: ForbiddenError
        """
        gestor = User.query.get(gestor_id)
        if not gestor or gestor.role != UserRole.GESTOR:
            raise ForbiddenError("Apenas gestores podem listar alunos")
        
        return Aluno.query.filter_by(prefeitura_id=gestor.prefeitura_id).all()