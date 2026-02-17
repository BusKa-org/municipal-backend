import uuid

import factory
from werkzeug.security import generate_password_hash

from app.models.enum import UserRole
from app.models.user import Gestor


class GestorFactory(factory.Factory):
    class Meta:
        model = Gestor

    id = factory.LazyFunction(uuid.uuid4)
    prefeitura_id = None
    nome = factory.Faker("name", locale="pt_BR")
    email = factory.Sequence(lambda n: f"gestor{n}@buska.test")
    senha_hash = factory.LazyAttribute(
        lambda o: generate_password_hash(getattr(o, "_raw_password", "StrongPass123!"))
    )
    cpf = factory.Faker("cpf", locale="pt_BR")
    telefone = factory.Faker("phone_number", locale="pt_BR")
    role = UserRole.GESTOR

    @classmethod
    def create_with_password(cls, password: str, **kwargs):
        kwargs["_raw_password"] = password
        return cls(**kwargs)
