from werkzeug.security import generate_password_hash

from app import create_app
from app.models.base import db
from app.models.enum import TipoInstituicao, UserRole
from app.models.geo import Endereco, Instituicao, Ponto
from app.models.prefeitura import Prefeitura
from app.models.user import Gestor

ID_PREFEITURA = "00000000-0000-0000-0000-000000000001"
ID_GESTOR = "00000000-0000-0000-0000-000000000002"
ID_PONTO_INST = "00000000-0000-0000-0000-000000000003"
ID_INSTITUICAO = "00000000-0000-0000-0000-000000000004"

app = create_app()


def seed_database():
    with app.app_context():
        print("Starting database seed...")

        if db.session.get(Prefeitura, ID_PREFEITURA):
            print("Data already exists. Skipping seed.")
            return

        print("Creating City Hall...")
        pref = Prefeitura(id=ID_PREFEITURA, nome="Prefeitura Matriz", estado="SP", ativo=True)
        db.session.add(pref)
        db.session.flush()  # Flush to make prefeitura available for foreign keys

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
            salario=15000.00,
        )

        db.session.add(admin_gestor)

        print("Creating Institution (Escola Municipal Centro)...")

        ponto_inst = Ponto(
            id=ID_PONTO_INST,
            prefeitura_id=ID_PREFEITURA,
            latitude=-23.5505,
            longitude=-46.6333,
            apelido="Escola Municipal Centro",
        )
        db.session.add(ponto_inst)

        instituicao = Instituicao(
            id=ID_INSTITUICAO,
            nome="Escola Municipal Centro",
            cnpj="00.000.000/0001-00",
            tipo=TipoInstituicao.ESCOLA_PUBLICA,
            ponto_id=ID_PONTO_INST,
        )
        db.session.add(instituicao)

        endereco_inst = Endereco(
            logradouro="Rua da Educação",
            numero="100",
            bairro="Centro",
            cidade="São Paulo",
            cep="01000000",
            ponto_id=ID_PONTO_INST,
        )
        db.session.add(endereco_inst)

        try:
            db.session.commit()
            print("Success! Database populated.")
            print("Login: admin@buska.app | Password: 123456")
            print(f"City Hall ID:    {ID_PREFEITURA}")
            print(f"Manager ID:      {ID_GESTOR}")
            print(f"Institution ID:  {ID_INSTITUICAO}")
        except Exception as e:
            db.session.rollback()
            print(f"Error populating database: {e}")


if __name__ == "__main__":
    seed_database()
