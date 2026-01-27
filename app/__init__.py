import json
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restx import Api
from sqlalchemy import text

from .api.controllers.aluno_controller import api as alunos_ns
from .api.controllers.auth_controller import api as auth_ns
from .api.controllers.instituicao_controller import api as inst_ns
from .api.controllers.onibus_controller import api as onibus_ns
from .api.controllers.pontos_controller import api as pontos_ns
from .api.controllers.rotas_controller import api as rotas_ns
from .api.controllers.user_controller import api as user_ns
from .api.controllers.viagens_controller import api as viagem_ns
from .core.config import settings
from .core.exceptions import AppError, ValidationError
from .models.base import db

jwt = JWTManager()


def create_app() -> Flask:
    app = Flask(__name__)

    load_dotenv()

    app.config["SQLALCHEMY_DATABASE_URI"] = settings.SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = settings.JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=settings.JWT_EXPIRES_HOURS)

    CORS(app)
    db.init_app(app)
    jwt.init_app(app)

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

    api.add_namespace(auth_ns, path="/auth")
    api.add_namespace(user_ns, path="/users")
    api.add_namespace(onibus_ns, path="/onibus")
    api.add_namespace(rotas_ns, path="/rotas")
    api.add_namespace(pontos_ns, path="/pontos")
    api.add_namespace(viagem_ns, path="/viagens")
    api.add_namespace(inst_ns, path="/instituicoes")
    api.add_namespace(alunos_ns, path="/alunos")

    # ==========================================
    # Error Handlers
    # ==========================================

    @app.errorhandler(AppError)
    def handle_app_error(error):
        """Handle all custom application errors."""
        response = {"error": error.message}
        if isinstance(error, ValidationError) and error.details:
            response["details"] = error.details
        return jsonify(response), error.status_code

    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({"error": "Recurso não encontrado"}), 404

    @app.errorhandler(500)
    def handle_internal_error(error):
        return jsonify({"error": "Erro interno do servidor"}), 500

    # ==========================================
    # OpenAPI Export Endpoint
    # ==========================================

    @app.route("/openapi.json")
    def openapi_spec():
        """Export OpenAPI specification as JSON."""
        return jsonify(api.__schema__)

    # ==========================================
    # CLI Commands
    # ==========================================

    @app.cli.command("init-db")
    def init_db():
        """Initialize database with seed data."""
        with app.app_context():
            try:
                print("[*] Executing population script...")
                with open("database/populate.sql", encoding="utf-8") as f:
                    sql_commands = f.read()
                db.session.execute(text(sql_commands))
                db.session.commit()
                print("[*] Database initialized successfully.")
            except FileNotFoundError:
                print("[!] Warning: database/populate.sql not found.")
            except Exception as e:
                print(f"[!] Error populating database: {e}")

    @app.cli.command("export-openapi")
    def export_openapi():
        """Export OpenAPI specification to docs/openapi.json."""
        with app.test_request_context():
            spec = api.__schema__
            output_path = "docs/openapi.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(spec, f, indent=2, ensure_ascii=False)
            print(f"[*] OpenAPI spec exported to {output_path}")

    return app
