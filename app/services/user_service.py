from werkzeug.security import generate_password_hash

from ..models.user import User
from ..models.municipio import Municipio
from ..models.base import db
import uuid


class UserService:

    @staticmethod
    def get_user_by_id(user_id: uuid):
        return User.query.get(user_id)

    @staticmethod
    def update_user(user_id: uuid, data: dict):
        user = User.query.get(user_id)
        if not user:
            return {"error": "user not found"}, 404

        nome = data.get("nome")
        email = data.get("email")
        password = data.get("password")
        municipio_id = data.get("municipio")

        # Apply updates
        if nome:
            user.nome = nome.strip()

        if email:
            user.email = email.lower().strip()

        if password:
            user.senha_hash = generate_password_hash(password.strip())

        if municipio_id:
            municipio = Municipio.query.filter_by(id=municipio_id).first()
            if not municipio:
                return {"error": f"Municipio with Name '{municipio_name}' not found"}, 404
            user.municipio_id = municipio.id

        db.session.commit()
        return {"message": "user updated successfully."}, 200

    @staticmethod
    def list_users(current_user_id: uuid):
        current_user = User.query.get(current_user_id)

        if not current_user or current_user.role != "gestor":
            return {"error": "Unauthorized"}, 403

        users = User.query.all()
        return ([
            {
                "id": u.id,
                "nome": u.nome,
                "email": u.email,
                "municipio": u.municipio_id,
                "role": u.role,
            }
            for u in users
        ], 200)
