import uuid
from werkzeug.security import generate_password_hash
from app import create_app
from app.models.base import db
from app.models.prefeitura import Prefeitura
from app.models.user import Gestor
from app.models.enum import UserRole

ID_PREFEITURA = "00000000-0000-0000-0000-000000000001"
ID_GESTOR     = "00000000-0000-0000-0000-000000000002"

app = create_app()

def seed_database():
    with app.app_context():
        print("Starting database seed...")

        if db.session.get(Prefeitura, ID_PREFEITURA):
            print("Data already exists. Skipping seed.")
            return

        print("Creating City Hall...")
        pref = Prefeitura(
            id=ID_PREFEITURA,
            nome="Prefeitura Matriz",
            estado="SP",
            ativo=True
        )
        db.session.add(pref)

        print("Creating Super Manager (admin@buska.app)...")
        
        secure_password = generate_password_hash("123456") 

        admin_gestor = Gestor(
            id=ID_GESTOR,
            prefeitura_id=ID_PREFEITURA,
            nome="Super Administrador",
            email="admin@buska.app",
            senha_hash=secure_password,
            cpf="000.000.000-00",
            telefone="11999999999",
            role=UserRole.GESTOR,
            
            matricula="SUPER-ADM-01",
            salario=15000.00
        )
        
        db.session.add(admin_gestor)

        try:
            db.session.commit()
            print("Success! Database populated.")
            print(f"Login: admin@buska.app | Password: 123456")
            print(f"City Hall ID: {ID_PREFEITURA}")
            print(f"Manager ID:   {ID_GESTOR}")
        except Exception as e:
            db.session.rollback()
            print(f"Error populating database: {e}")

if __name__ == "__main__":
    seed_database()