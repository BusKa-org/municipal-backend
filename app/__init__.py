from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_restx import Api
from datetime import timedelta
from dotenv import load_dotenv
from sqlalchemy import text
from .core.config import get_settings
from .models.base import db
from .api.controllers.auth_controller import api as auth_ns
from .api.controllers.user_controller import api as user_ns
from .api.controllers.onibus_controller import api as onibus_ns
from .api.controllers.rotas_controller import api as rotas_ns

jwt = JWTManager()

def create_app() -> Flask:
    app = Flask(__name__)

    settings = get_settings()
    load_dotenv()

    app.config["SQLALCHEMY_DATABASE_URI"] = settings.SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = settings.JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=settings.JWT_EXPIRES_HOURS)

    CORS(app)
    db.init_app(app)
    jwt.init_app(app)
    
    authorizations = {
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': "Digite no campo: Bearer <seu_token>"
        }
    }

    api = Api(app, 
        title='BusKá API', 
        version='1.0', 
        description='Buská API',
        doc='/docs',
        authorizations=authorizations,
        security='Bearer'
    )
    
    api.add_namespace(auth_ns, path='/auth')
    api.add_namespace(user_ns, path='/users')
    api.add_namespace(onibus_ns, path='/onibus')
    api.add_namespace(rotas_ns, path='/rotas')

    @app.cli.command("init-db")
    def init_db():
        """ Initialize database tables """
        with app.app_context():
            try:
                print("[*] Executing population script...")
                with open("database/populate.sql", "r", encoding="utf-8") as f:
                    sql_commands = f.read()
                db.session.execute(text(sql_commands))
                db.session.commit()
                print("[*] Database initialized successfully.")
            except FileNotFoundError:
                print("[!] Warning: database/populate.sql not found.")
            except Exception as e:
                print(f"[!] Error populating database: {e}")

    return app