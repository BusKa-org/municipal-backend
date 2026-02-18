"""Viagem endpoint documentation models."""

from flask_restx import fields


def register_models(api):
    """Register viagem models with the API namespace."""

    viagem_create_request = api.model(
        "ViagemCreateRequest",
        {
            "rota_id": fields.String(required=True, description="UUID da rota"),
            "horario_id": fields.String(required=True, description="UUID do horário"),
            "data": fields.String(required=True, description="Data (YYYY-MM-DD)"),
            "motorista_id": fields.String(description="UUID do motorista (opcional)"),
            "veiculo_id": fields.String(description="UUID do veículo (opcional)"),
        },
    )

    viagem_lote_request = api.model(
        "ViagemLoteRequest",
        {"data": fields.String(required=True, description="Data para gerar viagens (YYYY-MM-DD)")},
    )

    viagem_confirmacao_request = api.model(
        "ViagemConfirmacaoRequest",
        {
            "ponto_embarque_id": fields.String(
                required=True, description="UUID do ponto de embarque"
            )
        },
    )

    viagem_acao_request = api.model(
        "ViagemAcaoRequest",
        {"acao": fields.String(required=True, description="iniciar ou finalizar")},
    )

    viagem_response = api.model(
        "ViagemResponse",
        {
            "id": fields.String(description="UUID"),
            "data": fields.String(description="Data"),
            "horario_saida": fields.String(description="Horário"),
            "sentido": fields.String(description="Sentido"),
            "status": fields.String(description="AGENDADA, EM_ANDAMENTO, FINALIZADA"),
            "rota_id": fields.String(description="UUID da rota"),
            "rota_nome": fields.String(description="Nome da rota"),
            "motorista_id": fields.String(description="UUID do motorista"),
            "veiculo_id": fields.String(description="UUID do veículo"),
        },
    )

    ponto_embarque = api.model(
        "ViagemPontoEmbarque",
        {
            "id": fields.String(description="UUID do ponto"),
            "apelido": fields.String(description="Nome"),
            "ordem": fields.Integer(description="Ordem na rota"),
        },
    )

    viagem_list_response = api.model(
        "ViagemListResponse",
        {
            "items": fields.List(fields.Nested(viagem_response)),
            "total": fields.Integer(description="Total de viagens"),
        },
    )

    return {
        "viagem_create_request": viagem_create_request,
        "viagem_lote_request": viagem_lote_request,
        "viagem_confirmacao_request": viagem_confirmacao_request,
        "viagem_acao_request": viagem_acao_request,
        "viagem_response": viagem_response,
        "ponto_embarque": ponto_embarque,
        "viagem_list_response": viagem_list_response,
    }
