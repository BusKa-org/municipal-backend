"""User endpoint documentation models."""

from flask_restx import fields


def register_models(api):
    """Register user models with the API namespace."""

    response = api.model(
        "UserResponse",
        {
            "id": fields.String(description="UUID do usuário"),
            "prefeitura_id": fields.String(description="UUID da prefeitura"),
            "nome": fields.String(description="Nome completo"),
            "email": fields.String(description="Email"),
            "telefone": fields.String(description="Telefone"),
            "cpf": fields.String(description="CPF"),
            "role": fields.String(description="Perfil (ALUNO, MOTORISTA, GESTOR)"),
            "status": fields.String(description="Status (PENDING_SIGNUP, ACTIVE, DISABLED)"),
            "signup_completed_at": fields.DateTime(description="Data de conclusão do cadastro"),
            "matricula": fields.String(description="Matrícula (aluno)"),
            "nome_pai": fields.String(description="Nome do pai (aluno)"),
            "nome_mae": fields.String(description="Nome da mãe (aluno)"),
            "cnh": fields.String(description="CNH (motorista)"),
            "salario": fields.Float(description="Salário (motorista)"),
        },
    )

    motorista_create = api.model(
        "MotoristaCreateRequest",
        {
            "nome": fields.String(required=True, description="Nome completo"),
            "email": fields.String(required=True, description="Email"),
            "password": fields.String(required=True, description="Senha"),
            "cpf": fields.String(required=True, description="CPF"),
            "telefone": fields.String(description="Telefone"),
            "cnh": fields.String(required=True, description="CNH"),
            "salario": fields.Float(description="Salário"),
        },
    )

    change_password = api.model(
        "ChangePasswordRequest",
        {
            "current_password": fields.String(required=True, description="Senha atual"),
            "new_password": fields.String(required=True, description="Nova senha"),
        },
    )

    return {
        "response": response,
        "motorista_create": motorista_create,
        "change_password": change_password,
    }
