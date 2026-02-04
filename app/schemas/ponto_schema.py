from marshmallow import Schema, fields

# ==========================================
# Input Schemas (Validation)
# ==========================================


class PontoCreateSchema(Schema):
    """Schema for creating a new point."""

    apelido = fields.String(required=False, allow_none=True)
    latitude = fields.Float(required=True)
    longitude = fields.Float(required=True)


class PontoUpdateSchema(Schema):
    """Schema for updating a point (all fields optional)."""

    apelido = fields.String()
    latitude = fields.Float()
    longitude = fields.Float()


# ==========================================
# Response Schemas (Serialization)
# ==========================================


class PontoResponseSchema(Schema):
    id = fields.String()
    apelido = fields.String()
    latitude = fields.Float()
    longitude = fields.Float()
    endereco = fields.String(dump_default=None)
    instituicao = fields.String(dump_default=None)
