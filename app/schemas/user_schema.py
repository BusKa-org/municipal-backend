from marshmallow import Schema, fields, validate

class UserCreateSchema(Schema):
    prefeitura_id = fields.String(
        required=True, 
        metadata={"description": "UUID da Prefeitura"}
    )
    nome = fields.String(required=True)
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)
    
    telefone = fields.String(load_default=None)
    cpf = fields.String(required=True)
    
    role = fields.String(
        required=True, 
        validate=validate.OneOf(
            ["aluno", "motorista", "gestor", "ALUNO", "MOTORISTA", "GESTOR"]
        )
    )
    
    matricula = fields.String(load_default=None)
    nome_pai = fields.String(load_default=None)
    nome_mae = fields.String(load_default=None)
    cnh = fields.String(load_default=None)
    salario = fields.Float(load_default=None)


class UserResponseSchema(Schema):
    id = fields.String()
    prefeitura_id = fields.String()
    nome = fields.String()
    email = fields.String()
    telefone = fields.String()
    cpf = fields.String()
    
    role = fields.Method("get_role")

    matricula = fields.Method("get_matricula")
    nome_pai = fields.Method("get_nome_pai")
    nome_mae = fields.Method("get_nome_mae")
    cnh = fields.Method("get_cnh")
    salario = fields.Method("get_salario")

    def get_role(self, obj):
        return str(obj.role.value) if hasattr(obj.role, 'value') else str(obj.role)

    def get_matricula(self, obj):
        return getattr(obj, 'matricula', None)

    def get_nome_pai(self, obj):
        return getattr(obj, 'nome_pai', None)

    def get_nome_mae(self, obj):
        return getattr(obj, 'nome_mae', None)

    def get_cnh(self, obj):
        return getattr(obj, 'cnh', None)
        
    def get_salario(self, obj):
        val = getattr(obj, 'salario', None)
        return float(val) if val else None