from dataclasses import dataclass
from typing import Any

import pytest
from flask_jwt_extended import create_access_token
from sqlalchemy.pool import StaticPool

from app import create_app
from app.models.base import db
from tests.factories.prefeitura_factory import PrefeituraFactory
from tests.factories.user_factory import GestorFactory


class AuthenticatedClient:
    def __init__(self, flask_client, default_headers: dict[str, str]):
        self._client = flask_client
        self._default_headers = default_headers

    def _merge(self, headers: dict[str, str] | None):
        merged = dict(self._default_headers)
        if headers:
            merged.update(headers)
        return merged

    def get(self, *a, headers=None, **kw):
        return self._client.get(*a, headers=self._merge(headers), **kw)

    def post(self, *a, headers=None, **kw):
        return self._client.post(*a, headers=self._merge(headers), **kw)

    def put(self, *a, headers=None, **kw):
        return self._client.put(*a, headers=self._merge(headers), **kw)

    def patch(self, *a, headers=None, **kw):
        return self._client.patch(*a, headers=self._merge(headers), **kw)

    def delete(self, *a, headers=None, **kw):
        return self._client.delete(*a, headers=self._merge(headers), **kw)


@dataclass
class Actor:
    user: Any
    headers: dict[str, str]
    client: AuthenticatedClient


@pytest.fixture(scope="session")
def app():
    app = create_app()
    app.config.update(
        TESTING=True,
        DEBUG=True,
        JWT_SECRET_KEY="test-secret",
        SQLALCHEMY_DATABASE_URI="sqlite://",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        },
    )

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def _db(app):
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app, _db):
    return app.test_client()


@pytest.fixture()
def prefeitura(_db):
    p = PrefeituraFactory()
    _db.session.add(p)
    _db.session.commit()
    return p


@pytest.fixture()
def gestor(client, app, _db, prefeitura):
    u = GestorFactory(prefeitura_id=prefeitura.id)
    _db.session.add(u)
    _db.session.commit()

    with app.app_context():
        token = create_access_token(identity=str(u.id))

    headers = {"Authorization": f"Bearer {token}"}
    return Actor(user=u, headers=headers, client=AuthenticatedClient(client, headers))
