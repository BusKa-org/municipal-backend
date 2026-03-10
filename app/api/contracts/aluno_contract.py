"""Aluno endpoint documentation models."""

from flask_restx import fields


def register_models(api):
    """Register aluno models with the API namespace."""

    endereco_input = api.model(
        "EnderecoInput",
        {
            "rua": fields.String(description="Nome da rua"),
            "numero": fields.String(description="Número"),
            "bairro": fields.String(description="Bairro"),
            "cidade": fields.String(description="Cidade"),
            "estado": fields.String(description="Estado (UF)"),
            "cep": fields.String(description="CEP"),
            "complemento": fields.String(description="Complemento"),
        },
    )

    create_aluno_account_request = api.model(
        "AlunoAccountCreateRequest",
        {
            "nome": fields.String(required=True, description="Nome completo"),
            "email": fields.String(required=True, description="Email"),
            "password": fields.String(required=True, description="Senha"),
            "cpf": fields.String(required=True, description="CPF"),
            "telefone": fields.String(description="Telefone"),
        },
    )

    create_request = api.model(
        "AlunoCreateRequest",
        {
            "nome": fields.String(required=True, description="Nome completo"),
            "email": fields.String(required=True, description="Email"),
            "password": fields.String(required=True, description="Senha"),
            "cpf": fields.String(required=True, description="CPF"),
            "telefone": fields.String(description="Telefone"),
            "matricula": fields.String(required=True, description="Matrícula escolar"),
            "instituicao_id": fields.String(required=True, description="UUID da instituição"),
            "nome_pai": fields.String(description="Nome do pai"),
            "cpf_pai": fields.String(description="CPF do pai"),
            "nome_mae": fields.String(description="Nome da mãe"),
            "cpf_mae": fields.String(description="CPF da mãe"),
            "endereco_casa": fields.Nested(
                endereco_input, required=True, description="Endereço residencial"
            ),
        },
    )

    update_request = api.model(
        "AlunoUpdateRequest",
        {
            "nome": fields.String(description="Nome completo"),
            "telefone": fields.String(description="Telefone"),
            "matricula": fields.String(description="Matrícula escolar"),
            "nome_pai": fields.String(description="Nome do pai"),
            "cpf_pai": fields.String(description="CPF do pai"),
            "nome_mae": fields.String(description="Nome da mãe"),
            "cpf_mae": fields.String(description="CPF da mãe"),
            "endereco_casa": fields.Nested(endereco_input, description="Endereço residencial"),
        },
    )

    response = api.model(
        "AlunoResponse",
        {
            "id": fields.String(description="UUID do aluno"),
            "nome": fields.String(description="Nome completo"),
            "matricula": fields.String(description="Matrícula"),
            "escola": fields.String(description="Nome da escola"),
        },
    )

    return {
        "create_request": create_request,
        "create_aluno_account_request": create_aluno_account_request,
        "update_request": update_request,
        "response": response,
    }
