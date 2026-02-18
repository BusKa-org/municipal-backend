"""Aluno endpoint documentation models."""

from flask_restx import fields


def register_models(api):
    """Register aluno models with the API namespace."""

    endereco_input = api.model(
        "EnderecoInput",
        {
            "rua": fields.String(required=True, description="Nome da rua"),
            "numero": fields.String(required=True, description="Número"),
            "bairro": fields.String(required=True, description="Bairro"),
            "cidade": fields.String(required=True, description="Cidade"),
            "estado": fields.String(required=True, description="Estado (UF)"),
            "cep": fields.String(required=True, description="CEP"),
            "complemento": fields.String(required=False, description="Complemento"),
        },
    )

    aluno_provision_account_request = api.model(
        "AlunoProvisionAccountRequest",
        {
            "nome": fields.String(required=True, description="Nome completo"),
            "email": fields.String(required=True, description="Email"),
            "password": fields.String(required=True, description="Senha"),
            "cpf": fields.String(required=True, description="CPF"),
            "telefone": fields.String(description="Telefone"),
        },
    )

    self_signup_request = api.model(
        "AlunoSelfSignupRequest",
        {
            "nome": fields.String(required=True, description="Nome completo"),
            "email": fields.String(required=True, description="Email"),
            "password": fields.String(required=True, description="Senha"),
            "cpf": fields.String(required=True, description="CPF"),
            "telefone": fields.String(required=False, description="Telefone"),
            "matricula": fields.String(required=True, description="Matrícula escolar"),
            "instituicao_id": fields.String(required=True, description="UUID da instituição"),
            "nome_pai": fields.String(required=False, description="Nome do pai"),
            "cpf_pai": fields.String(required=False, description="CPF do pai"),
            "nome_mae": fields.String(required=False, description="Nome da mãe"),
            "cpf_mae": fields.String(required=False, description="CPF da mãe"),
            "endereco_casa": fields.Nested(endereco_input, required=True),
        },
    )

    me_update_request = api.model(
        "AlunoMeUpdateRequest",
        {
            "nome": fields.String(required=False, description="Nome completo"),
            "telefone": fields.String(required=False, description="Telefone"),
            "matricula": fields.String(required=False, description="Matrícula escolar"),
            "nome_pai": fields.String(required=False, description="Nome do pai"),
            "cpf_pai": fields.String(required=False, description="CPF do pai"),
            "nome_mae": fields.String(required=False, description="Nome da mãe"),
            "cpf_mae": fields.String(required=False, description="CPF da mãe"),
            "endereco_casa": fields.Nested(endereco_input, required=False),
        },
    )

    aluno_response = api.model(
        "AlunoResponse",
        {
            "id": fields.String(description="UUID do aluno"),
            "nome": fields.String(description="Nome completo"),
            "matricula": fields.String(description="Matrícula"),
            "escola": fields.String(description="Nome da escola"),
            "status": fields.String(description="Status (PENDING_SIGNUP, ACTIVE, DISABLED)"),
            "signup_completed_at": fields.DateTime(description="Data de conclusão do cadastro"),
        },
    )

    aluno_list_response = api.model(
        "AlunoListResponse",
        {
            "items": fields.List(fields.Nested(aluno_response)),
            "total": fields.Integer(description="Total de alunos"),
        },
    )

    return {
        "aluno_provision_account_request": aluno_provision_account_request,
        "self_signup_request": self_signup_request,
        "me_update_request": me_update_request,
        "aluno_response": aluno_response,
        "aluno_list_response": aluno_list_response,
    }
