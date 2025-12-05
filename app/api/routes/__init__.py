from flask import Blueprint

def register_routes(app):
    """Registers all route blueprints."""
    from .auth import auth_bp
    from .user import user_bp
    from .aluno import aluno_bp
    from .motorista import motorista_bp
    from .gestor import gestor_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(aluno_bp, url_prefix="/aluno")
    app.register_blueprint(user_bp, url_prefix="/user")
    app.register_blueprint(motorista_bp, url_prefix="/motorista")
    app.register_blueprint(gestor_bp, url_prefix="/gestor")
