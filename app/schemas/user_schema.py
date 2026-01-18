from marshmallow import Schema, fields, validate

class UserCreateSchema(Schema):
    nome = fields.String(required=True)
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)
    telefone = fields.String(missing=None)
    cpf = fields.String(required=True)
    
    role = fields.String(required=True, validate=validate.OneOf(["aluno", "motorista", "gestor"]))
    
    matricula = fields.String(missing=None)
    nome_pai = fields.String(missing=None)
    nome_mae = fields.String(missing=None)
    cnh = fields.String(missing=None)
    salario = fields.Float(missing=None)

class UserResponseSchema(Schema):
    id = fields.UUID(dump_only=True)
    nome = fields.String()
    email = fields.String()

    role = fields.Method("get_role")

    def get_role(self, obj):
        return obj.role