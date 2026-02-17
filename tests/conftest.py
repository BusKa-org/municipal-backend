import pytest

from app import create_app


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(
        TESTING=True,
        JWT_SECRET_KEY="test-secret-key-change-me",  # stops the weak key warning
    )
    return app


@pytest.fixture()
def client(app):
    return app.test_client()
