import pytest

from app.core.config import ConfigurationError, Settings


def test_frontend_url_vazio_falha_em_producao(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "a-long-and-strong-secret-for-tests")
    monkeypatch.setenv("FRONTEND_URL", "")

    with pytest.raises(ConfigurationError, match="FRONTEND_URL is required"):
        Settings()


def test_frontend_url_vazio_usa_padrao_fora_de_producao(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("FRONTEND_URL", "")

    settings = Settings()

    assert settings.FRONTEND_URL == "http://localhost:8081"
