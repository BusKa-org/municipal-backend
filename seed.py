"""
BusKa Database Seed Script

Creates initial test data for development and testing.
"""

import uuid
from datetime import date, time, timedelta

from werkzeug.security import generate_password_hash

from app import create_app
from app.models.base import db
from app.models.enum import SentidoViagem, StatusViagem, TipoInstituicao, UserRole
from app.models.geo import Endereco, Instituicao, Ponto
from app.models.onibus import Onibus
from app.models.prefeitura import Prefeitura
from app.models.rota import HorarioRota, Rota, RotaPonto
from app.models.user import Aluno, Gestor, Motorista
from app.models.viagem import Viagem

# Fixed UUIDs for predictable test data (as UUID objects)
ID_PREFEITURA = uuid.UUID("00000000-0000-0000-0000-000000000001")
ID_GESTOR = uuid.UUID("00000000-0000-0000-0000-000000000002")
ID_PONTO_INST = uuid.UUID("00000000-0000-0000-0000-000000000003")
ID_INSTITUICAO = uuid.UUID("00000000-0000-0000-0000-000000000004")
ID_MOTORISTA = uuid.UUID("00000000-0000-0000-0000-000000000005")
ID_ALUNO = uuid.UUID("00000000-0000-0000-0000-000000000006")
ID_ONIBUS = uuid.UUID("00000000-0000-0000-0000-000000000007")
ID_ROTA = uuid.UUID("00000000-0000-0000-0000-000000000008")
ID_PONTO_PARTIDA = uuid.UUID("00000000-0000-0000-0000-000000000009")
ID_PONTO_PARADA1 = uuid.UUID("00000000-0000-0000-0000-000000000010")
ID_PONTO_ALUNO = uuid.UUID("00000000-0000-0000-0000-000000000011")
ID_VIAGEM = uuid.UUID("00000000-0000-0000-0000-000000000012")
ID_HORARIO_ROTA = uuid.UUID("00000000-0000-0000-0000-000000000013")

app = create_app()
TEST_PASSWORD = "123456"


def seed_database():
    with app.app_context():
        print("\n" + "=" * 50)
        print("BusKa Database Seed")
        print("=" * 50 + "\n")

        if db.session.get(Prefeitura, ID_PREFEITURA):
            print("Data already exists. Skipping seed.\n")
            return

        secure_password = generate_password_hash(TEST_PASSWORD)

        # 1. Prefeitura
        print("1. Creating City Hall...")
        pref = Prefeitura(
            id=ID_PREFEITURA,
            nome="Prefeitura de Sao Paulo",
            estado="SP",
            ativo=True,
        )
        db.session.add(pref)
        db.session.flush()

        # 2. Gestor
        print("2. Creating Manager (admin@buska.app)...")
        admin_gestor = Gestor(
            id=ID_GESTOR,
            prefeitura_id=ID_PREFEITURA,
            nome="Maria Silva",
            email="admin@buska.app",
            senha_hash=secure_password,
            cpf="11111111111",
            telefone="11999990001",
            role=UserRole.GESTOR,
        )
        db.session.add(admin_gestor)

        # 3. Institution
        print("3. Creating Institution...")
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
            cnpj="11111111000111",
            tipo=TipoInstituicao.ESCOLA_PUBLICA,
            ponto_id=ID_PONTO_INST,
        )
        db.session.add(instituicao)

        endereco_inst = Endereco(
            logradouro="Rua da Educacao",
            numero="100",
            bairro="Centro",
            cidade="Sao Paulo",
            cep="01000000",
            ponto_id=ID_PONTO_INST,
        )
        db.session.add(endereco_inst)

        # 4. Onibus
        print("4. Creating Bus...")
        onibus = Onibus(
            id=ID_ONIBUS,
            prefeitura_id=ID_PREFEITURA,
            placa="ABC1234",
            modelo="Mercedes Sprinter",
            capacidade=20,
        )
        db.session.add(onibus)

        # 5. Motorista
        print("5. Creating Driver (motorista@buska.app)...")
        motorista = Motorista(
            id=ID_MOTORISTA,
            prefeitura_id=ID_PREFEITURA,
            nome="Joao Santos",
            email="motorista@buska.app",
            senha_hash=secure_password,
            cpf="22222222222",
            telefone="11999990002",
            role=UserRole.MOTORISTA,
            cnh="12345678901",
        )
        db.session.add(motorista)

        # 6. Route Stops
        print("6. Creating Route Stops...")
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
            apelido="Praca da Republica",
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

        # 7. Aluno
        print("7. Creating Student (aluno@buska.app)...")
        endereco_aluno = Endereco(
            logradouro="Rua das Flores",
            numero="42",
            bairro="Jardim Primavera",
            cidade="Sao Paulo",
            cep="01234000",
            ponto_id=ID_PONTO_ALUNO,
        )
        db.session.add(endereco_aluno)

        aluno = Aluno(
            id=ID_ALUNO,
            prefeitura_id=ID_PREFEITURA,
            nome="Pedro Oliveira",
            email="aluno@buska.app",
            senha_hash=secure_password,
            cpf="33333333333",
            telefone="11999990003",
            role=UserRole.ALUNO,
            matricula="ALU-2024-001",
            instituicao_id=ID_INSTITUICAO,
            ponto_casa_id=ID_PONTO_ALUNO,
        )
        db.session.add(aluno)

        # 8. Route
        print("8. Creating Route...")
        rota = Rota(
            id=ID_ROTA,
            prefeitura_id=ID_PREFEITURA,
            nome="Rota Centro - Manha",
            motorista_padrao_id=ID_MOTORISTA,
            veiculo_padrao_id=ID_ONIBUS,
        )
        db.session.add(rota)
        db.session.flush()

        # Add stops to route
        rota_ponto1 = RotaPonto(rota_id=ID_ROTA, ponto_id=ID_PONTO_PARTIDA, ordem=1)
        rota_ponto2 = RotaPonto(rota_id=ID_ROTA, ponto_id=ID_PONTO_PARADA1, ordem=2)
        rota_ponto3 = RotaPonto(rota_id=ID_ROTA, ponto_id=ID_PONTO_ALUNO, ordem=3)
        rota_ponto4 = RotaPonto(rota_id=ID_ROTA, ponto_id=ID_PONTO_INST, ordem=4)
        db.session.add_all([rota_ponto1, rota_ponto2, rota_ponto3, rota_ponto4])

        # 9. HorarioRota
        print("9. Creating Schedule...")
        horario_rota = HorarioRota(
            id=ID_HORARIO_ROTA,
            rota_id=ID_ROTA,
            horario_saida=time(6, 30),
            sentido=SentidoViagem.IDA,
        )
        db.session.add(horario_rota)
        db.session.flush()

        # 10. Viagem
        print("10. Creating Trip for tomorrow...")
        tomorrow = date.today() + timedelta(days=1)
        viagem = Viagem(
            id=ID_VIAGEM,
            data=tomorrow,
            horario_rota_id=ID_HORARIO_ROTA,
            motorista_id=ID_MOTORISTA,
            veiculo_id=ID_ONIBUS,
            status=StatusViagem.AGENDADA,
        )
        db.session.add(viagem)

        try:
            db.session.commit()
            print("\n" + "=" * 50)
            print("SUCCESS! Database populated.")
            print("=" * 50)
            print("\nTest Users (password: 123456):")
            print("  Gestor:    admin@buska.app")
            print("  Motorista: motorista@buska.app")
            print("  Aluno:     aluno@buska.app\n")
        except Exception as e:
            db.session.rollback()
            print(f"Error: {e}")
            raise


if __name__ == "__main__":
    seed_database()
