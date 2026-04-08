"""
BusKa Database Seed Script

Creates initial test data for development and testing.
Also supports importing Prefeituras and Instituicoes from CSV files.
"""

import os
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
from scripts.seeds.prefeituras_importer import import_prefeituras_csv
from scripts.seeds.instituicoes_importer import import_ies_csv, import_escolas_csv

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
TEST_PASSWORD = "buska123"  # min 8 chars required by backend validation


def should_import_prefeituras() -> bool:
    return (
        db.session.query(Prefeitura.id)
        .filter(Prefeitura.codigo_ibge.isnot(None))
        .first()
        is None
    )


def should_import_instituicoes() -> bool:
    return (
        db.session.query(Instituicao.id)
        .filter(Instituicao.fonte.in_(("EMEC", "INEP")))
        .first()
        is None
    )


def seed_catalog_from_csv() -> None:
    """
    Import prefeituras and instituicoes from CSV files, if needed and if paths are provided.

    Environment variables:
      - MUNICIPIOS_CSV_PATH
      - IES_CSV_PATH
      - ESCOLAS_CSV_PATH
    """
    municipios_csv_path = os.getenv("MUNICIPIOS_CSV_PATH")
    ies_csv_path = os.getenv("IES_CSV_PATH")
    escolas_csv_path = os.getenv("ESCOLAS_CSV_PATH")

    print("\n" + "=" * 50)
    print("Catalog Import")
    print("=" * 50)

    if should_import_prefeituras():
        if municipios_csv_path:
            print(f"Importing prefeituras from: {municipios_csv_path}")
            total_prefeituras = import_prefeituras_csv(municipios_csv_path)
            print(f"Prefeituras imported/updated: {total_prefeituras}")
        else:
            print("MUNICIPIOS_CSV_PATH not provided. Skipping prefeitura import.")
    else:
        print("Prefeituras already imported. Skipping prefeitura CSV import.")

    if should_import_instituicoes():
        if ies_csv_path:
            print(f"Importing IES from: {ies_csv_path}")
            total_ies = import_ies_csv(ies_csv_path)
            print(f"IES imported/updated: {total_ies}")
        else:
            print("IES_CSV_PATH not provided. Skipping IES import.")

        if escolas_csv_path:
            print(f"Importing schools from: {escolas_csv_path}")
            total_escolas = import_escolas_csv(escolas_csv_path)
            print(f"Schools imported/updated: {total_escolas}")
        else:
            print("ESCOLAS_CSV_PATH not provided. Skipping school import.")
    else:
        print("Instituicoes already imported. Skipping institution CSV import.")

    print("Catalog import finished.\n")


def get_or_create_demo_instituicao() -> Instituicao:
    """
    Reuse an imported institution from the demo prefeitura when available.
    Create a single manual fallback institution only if necessary.
    """
    instituicao = (
        db.session.query(Instituicao)
        .filter(
            Instituicao.prefeitura_id == ID_PREFEITURA,
            Instituicao.tipo.in_([
                TipoInstituicao.UNIVERSIDADE_PUBLICA,
                TipoInstituicao.UNIVERSIDADE_PRIVADA,
            ])
        )
        .first()
    )
    if not instituicao:
        instituicao = (
            db.session.query(Instituicao)
            .filter(Instituicao.prefeitura_id == ID_PREFEITURA)
            .order_by(Instituicao.nome.asc())
            .first()
        )

    if instituicao:
        print(f"Using existing institution for demo: {instituicao.nome}")
        return instituicao

    print("No institution found for demo prefeitura. Creating fallback institution...")

    ponto_inst = Ponto(
        id=ID_PONTO_INST,
        prefeitura_id=ID_PREFEITURA,
        latitude=-7.2167,
        longitude=-35.9097,
        apelido="Instituicao (Fallback)",
    )
    db.session.add(ponto_inst)

    instituicao = Instituicao(
        id=ID_INSTITUICAO,
        nome="Escola Municipal Centro",
        cnpj="11111111000111",
        tipo=TipoInstituicao.ESCOLA_PUBLICA,
        ponto_id=ID_PONTO_INST,
        fonte="MANUAL",
        codigo_externo=str(999012983901839028),
        uf="SP",
        prefeitura_id=ID_PREFEITURA,
        situacao="ATIVA",
        categoria_administrativa="Pública",
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

    db.session.flush()
    return instituicao


def seed_demo_data() -> None:
    """
    Create deterministic demo/test data used by development and testing.
    """
    global ID_PREFEITURA
    print("\n" + "=" * 50)
    print("BusKa Demo Seed")
    print("=" * 50 + "\n")

    if db.session.get(Prefeitura, ID_PREFEITURA):
        print("Demo data already exists. Skipping demo seed.\n")
        return

    secure_password = generate_password_hash(TEST_PASSWORD)

    # 1. Prefeitura
    print("1. Creating City Hall...")
    pref = (
        db.session.query(Prefeitura)
        .filter(Prefeitura.codigo_ibge == "2504009")
        .first()
    )

    if not pref:
        raise Exception("Campina Grande prefeitura not found in CSV import")

    ID_PREFEITURA = pref.id

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
    print("3. Resolving demo institution...")
    instituicao = get_or_create_demo_instituicao()

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
        latitude=-7.2306,
        longitude=-35.8811,
        apelido="Terminal Central CG",
    )
    db.session.add(ponto_partida)

    ponto_parada1 = Ponto(
        id=ID_PONTO_PARADA1,
        prefeitura_id=ID_PREFEITURA,
        latitude=-7.2280,
        longitude=-35.8670,
        apelido="Bairro Catolé",
    )
    db.session.add(ponto_parada1)

    ponto_aluno = Ponto(
        id=ID_PONTO_ALUNO,
        prefeitura_id=ID_PREFEITURA,
        latitude=-23.5520,
        longitude=-46.6350,
        apelido="Casa Aleatória",
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
        instituicao_id=instituicao.id,
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

    if instituicao.ponto_id:
        rota_ponto4 = RotaPonto(rota_id=ID_ROTA, ponto_id=instituicao.ponto_id, ordem=4)
        db.session.add(rota_ponto4)

    db.session.add_all([rota_ponto1, rota_ponto2, rota_ponto3])

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

    db.session.commit()

    print("\n" + "=" * 50)
    print("SUCCESS! Demo database populated.")
    print("=" * 50)
    print(f"\nTest Users (password: {TEST_PASSWORD}):")
    print("  Gestor:    admin@buska.app")
    print("  Motorista: motorista@buska.app")
    print("  Aluno:     aluno@buska.app")
    print(f"\nDemo institution used: {instituicao.nome}\n")


def seed_database() -> None:
    with app.app_context():
        print("\n" + "=" * 50)
        print("BusKa Database Seed")
        print("=" * 50)

        try:
            seed_catalog_from_csv()
            seed_demo_data()
        except Exception as e:
            db.session.rollback()
            print(f"Error: {e}")
            raise


if __name__ == "__main__":
    seed_database()