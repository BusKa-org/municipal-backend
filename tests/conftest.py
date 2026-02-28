import pytest

from app import create_app


@pytest.fixture(scope="session")
def app():
    """
    scope='session'
    garante que o create_app() (e o APScheduler) rodem
    apenas uma única vez para todos os testes do BusKá.
    """
    app = create_app()
    with app.app_context():
        yield app
