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
    
    # Polymorphic fields (may not exist on all User subtypes)
    matricula = fields.String(dump_default=None)
    nome_pai = fields.String(dump_default=None)
    nome_mae = fields.String(dump_default=None)
    cnh = fields.String(dump_default=None)
    salario = fields.Float(dump_default=None)

    def get_role(self, obj):
        return str(obj.role.value) if hasattr(obj.role, 'value') else str(obj.role)