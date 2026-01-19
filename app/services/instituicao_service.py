from app.models.geo import Instituicao, Endereco, Ponto
from app.models.user import User
from app.models.base import db

class InstituicaoService:
    
    @staticmethod
    def create_instituicao(gestor_id, data):
        user = User.query.get(gestor_id)
        if not user or str(user.role) != 'GESTOR':
            return {"error": "Permissão negada. Apenas gestores criam instituições."}, 403

        nome = data.get('nome')
        cnpj = data.get('cnpj')
        tipo_str = data.get('tipo', 'ESCOLA_PUBLICA')
        end_data = data.get('endereco')

        if not end_data:
            return {"error": "Dados de endereço são obrigatórios"}, 400

        novo_ponto = Ponto(
            prefeitura_id=user.prefeitura_id,
            latitude=end_data.get('latitude'),
            longitude=end_data.get('longitude'),
            apelido=f"Inst: {nome}"
        )
        db.session.add(novo_ponto)
        db.session.flush()

        nova_inst = Instituicao(
            nome=nome,
            cnpj=cnpj,
            tipo=TipoInstituicao(tipo_str),
            ponto_id=novo_ponto.id
        )
        db.session.add(nova_inst)

        novo_endereco = Endereco(
            logradouro=end_data.get('logradouro'),
            numero=end_data.get('numero'),
            bairro=end_data.get('bairro'),
            cidade=end_data.get('cidade'),
            cep=end_data.get('cep'),
            ponto_id=novo_ponto.id
        )
        db.session.add(novo_endereco)

        try:
            db.session.commit()
            return nova_inst, 201
        except Exception as e:
            db.session.rollback()
            return {"error": "Erro ao salvar dados", "details": str(e)}, 500

    @staticmethod
    def list_all(gestor_id):
        user = User.query.get(gestor_id)
        if not user: return {"error": "Usuário não encontrado"}, 403

        instituicoes = (
            Instituicao.query
            .join(Ponto)
            .filter(Ponto.prefeitura_id == user.prefeitura_id)
            .all()
        )
        
        return instituicoes, 200

    @staticmethod
    def get_by_id(gestor_id, inst_id):
        user = User.query.get(gestor_id)
        inst = Instituicao.query.get(inst_id)
        
        if not inst: return {"error": "Instituição não encontrada"}, 404
        
        if inst.ponto.prefeitura_id != user.prefeitura_id:
            return {"error": "Acesso negado"}, 403
            
        return inst, 200

    @staticmethod
    def delete_instituicao(gestor_id, inst_id):
        user = User.query.get(gestor_id)
        if str(user.role) != 'GESTOR': return {"error": "Proibido"}, 403

        inst = Instituicao.query.get(inst_id)
        if not inst: return {"error": "Não encontrado"}, 404

        if inst.ponto.prefeitura_id != user.prefeitura_id:
            return {"error": "Acesso negado"}, 403

        db.session.delete(inst.ponto)
        db.session.commit()
        
        return {"message": "Instituição removida com sucesso"}, 200