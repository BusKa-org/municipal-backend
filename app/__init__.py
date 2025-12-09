from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flasgger import Swagger
from geoalchemy2 import Geometry
from datetime import timedelta
from dotenv import load_dotenv
from sqlalchemy import text

from .api.routes import register_routes
from .core.config import get_settings
from .models.base import db

jwt = JWTManager()

def create_app() -> Flask:
    app = Flask(__name__)
    swagger = Swagger(app)

    settings = get_settings()
    load_dotenv()

    app.config["SQLALCHEMY_DATABASE_URI"] = settings.SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = settings.JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=settings.JWT_EXPIRES_HOURS)

    CORS(app)
    db.init_app(app)
    jwt.init_app(app)

    register_routes(app)

    @app.cli.command("init-db")
    def init_db():
        """ Initialize database tables """
        with app.app_context():
            db.create_all()
            with open("database/populate.sql", "r", encoding="utf-8") as f:
                sql_commands = f.read()
            db.session.execute(text(sql_commands))
            db.session.commit()
            print("[*] Database initialized successfully.")

    return app
