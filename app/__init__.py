import json
import logging
from datetime import timedelta
from typing import Any

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials
from flask import Flask, Response, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restx import Api

from app.core.error_handlers import register_error_handlers, register_jwt_handlers
from app.extensions import scheduler
from app.tasks.notificacao_tasks import verificar_viagens_10min, verificar_viagens_24h

from .api.controllers.aluno_controller import api as alunos_ns
from .api.controllers.auth_controller import api as auth_ns
from .api.controllers.instituicao_controller import api as inst_ns
from .api.controllers.notificacao_controller import api as notificacoes_ns
from .api.controllers.onibus_controller import api as onibus_ns
from .api.controllers.pontos_controller import api as pontos_ns
from .api.controllers.rotas_controller import api as rotas_ns
from .api.controllers.user_controller import api as user_ns
from .api.controllers.viagens_controller import api as viagem_ns
from .core.config import settings
from .models.base import db
from .utils import (
    check_production_security,
    setup_logging,
    setup_request_id_middleware,
    setup_security_headers,
)

jwt = JWTManager()
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)

    load_dotenv()

    if not firebase_admin._apps:
        if settings.FIREBASE_CREDENTIALS:
            cert_dict = json.loads(settings.FIREBASE_CREDENTIALS)
            cred = credentials.Certificate(cert_dict)
            logger.info("Firebase initialized via GitHub Secrets (Environment Variable).")
        else:
            cred = credentials.Certificate("firebase-credentials.json")
            logger.info("Firebase initialized via local file.")

        firebase_admin.initialize_app(cred)

    app.config["SQLALCHEMY_DATABASE_URI"] = settings.SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = settings.JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=settings.JWT_EXPIRES_HOURS)
    app.config["DEBUG"] = settings.DEBUG

    # ==========================================
    # Logging Configuration
    # ==========================================
    setup_logging(app)
    setup_request_id_middleware(app)

    logger.info(
        "Application starting",
        extra={
            "environment": settings.ENV,
            "debug": settings.DEBUG,
        },
    )

    # ==========================================
    # CORS Configuration
    # ==========================================
    CORS(
        app,
        origins=settings.CORS_ORIGINS,
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        max_age=86400,  # Cache preflight for 24 hours
    )

    db.init_app(app)
    jwt.init_app(app)

    scheduler.init_app(app)
    scheduler.start()

    scheduler.add_job(
        id="job_24h", func=verificar_viagens_24h, args=[app], trigger="interval", minutes=60
    )

    scheduler.add_job(
        id="job_10min", func=verificar_viagens_10min, args=[app], trigger="interval", minutes=2
    )

    # ==========================================
    # Security Headers
    # ==========================================
    setup_security_headers(app)

    # Set maximum request size (16MB)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

    # Check production security
    if not settings.DEBUG:
        security_warnings = check_production_security(app)
        if security_warnings:
            logger.warning(
                "Security configuration warnings",
                extra={"warnings": security_warnings},
            )

    authorizations = {
        "Bearer": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "JWT token. Format: Bearer <token>",
        }
    }

    api = Api(
        app,
        title="BusKá API",
        version="1.0.0",
        description="""
## Sistema de Gerenciamento de Transporte Escolar

API para gerenciamento de rotas, viagens e alunos do transporte escolar municipal.

### Autenticação
Todos os endpoints (exceto `/auth/login`) requerem autenticação JWT.
Inclua o header: `Authorization: Bearer <seu_token>`

### Roles
- **ALUNO**: Visualiza rotas, confirma presença em viagens
- **MOTORISTA**: Gerencia viagens atribuídas, inicia/finaliza trajetos
- **GESTOR**: Acesso completo à prefeitura (CRUD de rotas, motoristas, relatórios)
        """,
        doc="/docs",
        authorizations=authorizations,
        security="Bearer",
        contact="BusKá Team",
    )

    # API v1 routes
    api.add_namespace(auth_ns, path="/v1/auth")
    api.add_namespace(user_ns, path="/v1/users")
    api.add_namespace(notificacoes_ns, path="/v1/notificacoes")
    api.add_namespace(onibus_ns, path="/v1/onibus")
    api.add_namespace(rotas_ns, path="/v1/rotas")
    api.add_namespace(pontos_ns, path="/v1/pontos")
    api.add_namespace(viagem_ns, path="/v1/viagens")
    api.add_namespace(inst_ns, path="/v1/instituicoes")
    api.add_namespace(alunos_ns, path="/v1/alunos")

    # ==========================================
    # Error Handlers
    # ==========================================

    register_jwt_handlers(jwt)
    register_error_handlers(app)

    # ==========================================
    # OpenAPI Export Endpoint
    # ==========================================

    @app.route("/openapi.json")
    def openapi_spec() -> Any:
        """Export OpenAPI specification as JSON."""
        return jsonify(api.__schema__)

    # ==========================================
    # CLI Commands
    # ==========================================

    @app.cli.command("export-openapi")
    def export_openapi() -> None:
        """Export OpenAPI specification to docs/openapi.json."""
        with app.test_request_context():
            spec = api.__schema__
            output_path = "docs/openapi.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(spec, f, indent=2, ensure_ascii=False)
            print(f"[*] OpenAPI spec exported to {output_path}")

    # ==========================================
    # Health / Readiness Endpoints
    # ==========================================

    @app.get("/health")
    def health() -> tuple[Response, int]:
        """Liveness probe — server is running."""
        return (
            jsonify(
                status="ok",
                service="buska-backend",
                environment=settings.ENV,
            ),
            200,
        )

    @app.get("/ready")
    def ready() -> tuple[Response, int]:
        """Readiness probe — server can handle requests (DB reachable)."""
        try:
            # Minimal DB check (safe + fast)
            from sqlalchemy import text

            db.session.execute(text("SELECT 1"))
            return jsonify(status="ok", ready=True), 200
        except Exception:
            logger.error("Readiness check failed", exc_info=True)
            return jsonify(status="error", ready=False), 503

    return app
