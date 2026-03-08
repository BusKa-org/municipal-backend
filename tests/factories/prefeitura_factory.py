import uuid

import factory

from app.models.prefeitura import Prefeitura


class PrefeituraFactory(factory.Factory):
    class Meta:
        model = Prefeitura

    id = factory.LazyFunction(uuid.uuid4)
    nome = factory.Sequence(lambda n: f"Prefeitura Teste {n}")
    estado = "PB"
    ativo = True
