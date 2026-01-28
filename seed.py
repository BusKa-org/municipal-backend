"""
BusKá Database Seed Script

Creates initial test data for development and testing:
- Prefeitura (City Hall)
- Gestor (Manager/Admin)
- Motorista (Driver)
- Aluno (Student)
- Instituição (School)
- Rotas (Routes)
- Pontos (Stops)
- Viagens (Trips)
"""

from datetime import date, time, timedelta

from werkzeug.security import generate_password_hash

from app import create_app
from app.models.base import db
from app.models.enum import StatusViagem, TipoInstituicao, UserRole
from app.models.geo import Endereco, Instituicao, Ponto
from app.models.prefeitura import Prefeitura
from app.models.transporte import Horario, Onibus, Rota, RotaPonto, Viagem
from app.models.user import Aluno, Gestor, Motorista

# Fixed UUIDs for predictable test data
ID_PREFEITURA = "00000000-0000-0000-0000-000000000001"
ID_GESTOR = "00000000-0000-0000-0000-000000000002"
ID_PONTO_INST = "00000000-0000-0000-0000-000000000003"
ID_INSTITUICAO = "00000000-0000-0000-0000-000000000004"
ID_MOTORISTA = "00000000-0000-0000-0000-000000000005"
ID_ALUNO = "00000000-0000-0000-0000-000000000006"
ID_ONIBUS = "00000000-0000-0000-0000-000000000007"
ID_ROTA = "00000000-0000-0000-0000-000000000008"
ID_PONTO_PARTIDA = "00000000-0000-0000-0000-000000000009"
ID_PONTO_PARADA1 = "00000000-0000-0000-0000-000000000010"
ID_PONTO_ALUNO = "00000000-0000-0000-0000-000000000011"
ID_VIAGEM = "00000000-0000-0000-0000-000000000012"
ID_HORARIO = "00000000-0000-0000-0000-000000000013"

app = create_app()

# Common password for all test users
TEST_PASSWORD = "123456"


def seed_database():
    """Main seed function - creates all test data."""
    with app.app_context():
        print("\n" + "=" * 50)
        print("🚌 BusKá Database Seed")
        print("=" * 50 + "\n")

        if db.session.get(Prefeitura, ID_PREFEITURA):
            print("⚠️  Data already exists. Skipping seed.")
            print("   To reseed, drop the database first.\n")
            return

        secure_password = generate_password_hash(TEST_PASSWORD)

        # 1. Create Prefeitura (City Hall)
        print("1️⃣  Creating City Hall...")
        pref = Prefeitura(
            id=ID_PREFEITURA, nome="Prefeitura de São Paulo - Matriz", estado="SP", ativo=True
        )
        db.session.add(pref)
        db.session.flush()

        # 2. Create Gestor (Manager)
        print("2️⃣  Creating Manager (admin@buska.app)...")
        admin_gestor = Gestor(
            id=ID_GESTOR,
            prefeitura_id=ID_PREFEITURA,
            nome="Maria Silva - Gestora",
            email="admin@buska.app",
            senha_hash=secure_password,
            cpf="111.111.111-11",
            telefone="11999990001",
            role=UserRole.GESTOR,
            matricula="GESTOR-001",
            salario=12000.00,
        )
        db.session.add(admin_gestor)

        # 3. Create Institution (School)
        print("3️⃣  Creating Institution...")
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
            cnpj="11.111.111/0001-11",
            tipo=TipoInstituicao.ESCOLA_PUBLICA,
            ponto_id=ID_PONTO_INST,
        )
        db.session.add(instituicao)

        endereco_inst = Endereco(
            logradouro="Rua da Educação",
            numero="100",
            bairro="Centro",
            cidade="São Paulo",
            cep="01000-000",
            ponto_id=ID_PONTO_INST,
        )
        db.session.add(endereco_inst)

        # 4. Create Onibus (Bus)
        print("4️⃣  Creating Bus...")
        onibus = Onibus(
            id=ID_ONIBUS,
            prefeitura_id=ID_PREFEITURA,
            placa="ABC-1234",
            modelo="Mercedes Sprinter",
            capacidade=20,
            ano=2022,
            ativo=True,
        )
        db.session.add(onibus)

        # 5. Create Motorista (Driver)
        print("5️⃣  Creating Driver (motorista@buska.app)...")
        motorista = Motorista(
            id=ID_MOTORISTA,
            prefeitura_id=ID_PREFEITURA,
            nome="João Santos - Motorista",
            email="motorista@buska.app",
            senha_hash=secure_password,
            cpf="222.222.222-22",
            telefone="11999990002",
            role=UserRole.MOTORISTA,
            cnh="12345678901",
            categoria_cnh="D",
            validade_cnh=date.today() + timedelta(days=365 * 2),
            onibus_id=ID_ONIBUS,
        )
        db.session.add(motorista)

        # 6. Create Route Stops
        print("6️⃣  Creating Route Stops...")
        ponto_partida = Ponto(
            id=ID_PONTO_PARTIDA,
            prefeitura_id=ID_PREFEITURA,
            latitude=-23.5600,
            longitude=-46.6400,
            apelido="Terminal Central",
        )
        db.session.add(ponto_partida)

        ponto_parada1 = Ponto(
            id=ID_PONTO_PARADA1,
            prefeitura_id=ID_PREFEITURA,
            latitude=-23.5550,
            longitude=-46.6370,
            apelido="Praça da República",
        )
        db.session.add(ponto_parada1)

        ponto_aluno = Ponto(
            id=ID_PONTO_ALUNO,
            prefeitura_id=ID_PREFEITURA,
            latitude=-23.5520,
            longitude=-46.6350,
            apelido="Casa do Aluno",
        )
        db.session.add(ponto_aluno)

        # 7. Create Aluno (Student)
        print("7️⃣  Creating Student (aluno@buska.app)...")
        endereco_aluno = Endereco(
            logradouro="Rua das Flores",
            numero="42",
            bairro="Jardim Primavera",
            cidade="São Paulo",
            cep="01234-000",
            ponto_id=ID_PONTO_ALUNO,
        )
        db.session.add(endereco_aluno)

        aluno = Aluno(
            id=ID_ALUNO,
            prefeitura_id=ID_PREFEITURA,
            nome="Pedro Oliveira - Aluno",
            email="aluno@buska.app",
            senha_hash=secure_password,
            cpf="333.333.333-33",
            telefone="11999990003",
            role=UserRole.ALUNO,
            matricula="ALU-2024-001",
            serie="9º Ano",
            turno="Manhã",
            instituicao_id=ID_INSTITUICAO,
            ponto_embarque_id=ID_PONTO_ALUNO,
            responsavel_nome="Ana Oliveira",
            responsavel_telefone="11999990004",
        )
        db.session.add(aluno)

        # 8. Create Horario
        print("8️⃣  Creating Schedule...")
        horario = Horario(
            id=ID_HORARIO,
            prefeitura_id=ID_PREFEITURA,
            nome="Manhã - Ida",
            horario_inicio=time(6, 30),
            horario_fim=time(7, 30),
        )
        db.session.add(horario)

        # 9. Create Route
        print("9️⃣  Creating Route...")
        rota = Rota(
            id=ID_ROTA,
            prefeitura_id=ID_PREFEITURA,
            motorista_id=ID_MOTORISTA,
            nome="Rota Centro - Manhã",
            descricao="Rota principal do centro para a Escola Municipal",
            ativa=True,
        )
        db.session.add(rota)
        db.session.flush()

        # Add stops to route
        rota_ponto1 = RotaPonto(
            rota_id=ID_ROTA,
            ponto_id=ID_PONTO_PARTIDA,
            ordem=1,
        )
        rota_ponto2 = RotaPonto(
            rota_id=ID_ROTA,
            ponto_id=ID_PONTO_PARADA1,
            ordem=2,
        )
        rota_ponto3 = RotaPonto(
            rota_id=ID_ROTA,
            ponto_id=ID_PONTO_ALUNO,
            ordem=3,
        )
        rota_ponto4 = RotaPonto(
            rota_id=ID_ROTA,
            ponto_id=ID_PONTO_INST,
            ordem=4,
        )
        db.session.add_all([rota_ponto1, rota_ponto2, rota_ponto3, rota_ponto4])

        # 10. Create Trip
        print("🔟 Creating Trip for tomorrow...")
        tomorrow = date.today() + timedelta(days=1)
        viagem = Viagem(
            id=ID_VIAGEM,
            prefeitura_id=ID_PREFEITURA,
            rota_id=ID_ROTA,
            motorista_id=ID_MOTORISTA,
            horario_id=ID_HORARIO,
            data=tomorrow,
            tipo="IDA",
            status=StatusViagem.AGENDADA,
        )
        db.session.add(viagem)

        # Commit all changes
        try:
            db.session.commit()
            print("\n" + "=" * 50)
            print("✅ SUCCESS! Database populated with test data.")
            print("=" * 50)
            print("\n📋 Test Users (password: 123456 for all):")
            print("-" * 50)
            print("   👨‍💼 Gestor:    admin@buska.app")
            print("   🚗 Motorista: motorista@buska.app")
            print("   🎓 Aluno:     aluno@buska.app")
            print("-" * 50)
            print("\n📊 Created Resources:")
            print(f"   • Prefeitura: {ID_PREFEITURA}")
            print(f"   • Instituição: {ID_INSTITUICAO}")
            print("   • Ônibus: ABC-1234")
            print("   • Rota: Rota Centro - Manhã")
            print(f"   • Viagem agendada para: {tomorrow.strftime('%d/%m/%Y')}")
            print("\n")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error populating database: {e}")
            raise


def clear_database():
    """Clear all data from the database (use with caution!)."""
    with app.app_context():
        print("\n⚠️  Clearing database...")
        db.drop_all()
        db.create_all()
        print("✅ Database cleared and recreated.\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        clear_database()

    seed_database()
