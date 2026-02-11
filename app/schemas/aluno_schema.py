from marshmallow import Schema, fields

from app.schemas.endereco_schema import EnderecoInputSchema


class AlunoCreateSchema(Schema):
    nome = fields.String(required=True)
    email = fields.Email(required=True)
    password = fields.String(required=True)
    cpf = fields.String(required=True)
    telefone = fields.String()

    matricula = fields.String(required=True)
    instituicao_id = fields.String(required=True)

    nome_pai = fields.String()
    cpf_pai = fields.String()
    nome_mae = fields.String()
    cpf_mae = fields.String()

    endereco_casa = fields.Nested(EnderecoInputSchema, required=True)


class AlunoResponseSchema(Schema):
    id = fields.String()
    nome = fields.String()
    matricula = fields.String()
    escola = fields.String(attribute="instituicao.nome")


class AlunoUpdateSchema(Schema):

    nome = fields.String()
    telefone = fields.String()

    matricula = fields.String()
    nome_pai = fields.String()
    cpf_pai = fields.String()
    nome_mae = fields.String()
    cpf_mae = fields.String()

    endereco_casa = fields.Nested(EnderecoInputSchema)
