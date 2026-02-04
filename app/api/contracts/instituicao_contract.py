"""Instituicao endpoint documentation models."""

from flask_restx import fields


def register_models(api):
    """Register instituicao models with the API namespace."""

    endereco_input = api.model(
        "InstituicaoEnderecoInput",
        {
            "rua": fields.String(description="Nome da rua"),
            "numero": fields.String(description="Número"),
            "bairro": fields.String(description="Bairro"),
            "cidade": fields.String(description="Cidade"),
            "estado": fields.String(description="Estado (UF)"),
            "cep": fields.String(description="CEP"),
        },
    )

    create_request = api.model(
        "InstituicaoCreateRequest",
        {
            "nome": fields.String(required=True, description="Nome da instituição"),
            "tipo": fields.String(description="Tipo (ESCOLA, CRECHE, UNIVERSIDADE)"),
            "endereco": fields.Nested(endereco_input, required=True, description="Endereço"),
        },
    )

    response = api.model(
        "InstituicaoResponse",
        {
            "id": fields.String(description="UUID"),
            "nome": fields.String(description="Nome"),
            "tipo": fields.String(description="Tipo"),
            "endereco": fields.String(description="Endereço formatado"),
        },
    )

    return {"create_request": create_request, "response": response}
