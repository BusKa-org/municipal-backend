from flask import request
from flask_restx import Resource, Namespace
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.aluno_service import AlunoService
from app.schemas.aluno_schema import AlunoCreateSchema, AlunoResponseSchema, AlunoUpdateSchema
from app.api.contracts.aluno_contract import AlunoContract

api = Namespace('alunos', description='Área do Aluno (App)')

create_schema = AlunoCreateSchema()
response_schema = AlunoResponseSchema()
list_response_schema = AlunoResponseSchema(many=True)
update_schema = AlunoUpdateSchema()

create_model = AlunoContract.create_model(api)
update_model = AlunoContract.update_model(api)

@api.route('/signup')
class AlunoSignupResource(Resource):
    @api.doc('aluno_signup', security=[]) 
    @api.expect(create_model)
    def post(self):
        """Auto-cadastro do Aluno (Público)"""
        data = request.get_json()
        
        errors = create_schema.validate(data)
        if errors: return {"error": "Erro de validação", "details": errors}, 400
        
        result, status = AlunoService.auto_cadastro(data)
        if status != 201: return result, status
        
        return response_schema.dump(result), 201

@api.route('/me')
class AlunoMeResource(Resource):
    @api.doc('aluno_profile')
    @api.expect(update_model, jwt_required=True) 
    @jwt_required()
    def put(self):
        """Aluno atualiza seu perfil (Dados Pessoais + Endereço)"""
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validação parcial (Marshmallow)
        errors = update_schema.validate(data)
        if errors: return {"error": "Validation error", "details": errors}, 400
        
        result, status = AlunoService.update_me(user_id, data)
        if status != 200: return result, status
        
        return response_schema.dump(result), 200

    @api.doc('aluno_delete')
    @api.expect(jwt_required=True)
    @jwt_required()
    def delete(self):
        """Aluno exclui sua conta"""
        user_id = get_jwt_identity()
        return AlunoService.delete_me(user_id)

@api.route('/')
class AlunoListResource(Resource):
    @api.doc('list_alunos_gestor')
    @api.expect(jwt_required=True)
    @jwt_required()
    def get(self):
        """Gestor vê lista de alunos cadastrados"""
        user_id = get_jwt_identity()
        result, status = AlunoService.list_alunos_gestor(user_id)
        if status != 200: return result, status
        return list_response_schema.dump(result), 200