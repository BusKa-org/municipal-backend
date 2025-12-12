from flask import Blueprint

def register_routes(app):
    """Registers all route blueprints."""
    from .auth import auth_bp
    from .user import user_bp
    from .me import self_bp
    from .rotas import rotas_bp
    from .viagens import viagens_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(user_bp, url_prefix="/user")
    app.register_blueprint(self_bp, url_prefix="/me")
    app.register_blueprint(self_bp, url_prefix="/rotas")
    app.register_blueprint(self_bp, url_prefix="/viagens")
