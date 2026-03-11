"""
BusKa Database Super Seed Script - Campina Grande & Galante

Creates initial test data for development and testing, featuring
historical telemetry, active trips, and future scheduled trips.
"""

import random
import uuid
from datetime import UTC, datetime, time, timedelta

from werkzeug.security import generate_password_hash

from app import create_app
from app.models.base import db
from app.models.enum import (
    DiaDaSemana,
    SentidoViagem,
    StatusViagem,
    TipoInstituicao,
    UserRole,
    UserStatus,
)
from app.models.geo import Instituicao, Ponto
from app.models.onibus import Onibus
from app.models.prefeitura import Prefeitura
from app.models.rota import DiasOperacao, HorarioRota, Rota, RotaAluno, RotaPonto
from app.models.user import Aluno, Gestor, Motorista
from app.models.viagem import AlunosConfirmados, TelemetriaViagem, Viagem, ViagemPonto

# Fixed UUIDs for predictable test data
ID_PREF_CG = uuid.UUID("c0000000-0000-0000-0000-000000000001")
ID_GESTOR_CG = uuid.UUID("c0000000-0000-0000-0000-000000000002")
ID_BUS_CG = uuid.UUID("c0000000-0000-0000-0000-000000000003")
ID_DRIVER_CG = uuid.UUID("c0000000-0000-0000-0000-000000000004")
ID_ROUTE_CG = uuid.UUID("c0000000-0000-0000-0000-000000000005")

app = create_app()
TEST_PASSWORD = "123456"


def interpolate_coordinates(ponto_a, ponto_b, steps):
    """Generates intermediate GPS points for a realistic map line."""
    lat_step = (ponto_b[0] - ponto_a[0]) / steps
    lon_step = (ponto_b[1] - ponto_a[1]) / steps
    return [(ponto_a[0] + lat_step * i, ponto_a[1] + lon_step * i) for i in range(steps)]


def seed_database():
    with app.app_context():
        print("\n" + "=" * 50)
        print("BusKa Database Super Seed - Campina Grande")
        print("=" * 50 + "\n")

        secure_password = generate_password_hash(TEST_PASSWORD)

        try:
            # 1. City Hall
            print("1. Creating City Hall...")
            city_hall = Prefeitura(
                id=ID_PREF_CG,
                nome="Prefeitura de Campina Grande",
                estado="PB",
                ativo=True,
            )
            db.session.add(city_hall)
            db.session.flush()

            # 2. Manager
            print("2. Creating Manager (gestor.cg@buska.app)...")
            manager = Gestor(
                id=ID_GESTOR_CG,
                prefeitura_id=ID_PREF_CG,
                nome="Bruno Romero",
                email="gestor.cg@buska.app",
                senha_hash=secure_password,
                cpf="11111111112",
                telefone="83999990001",
                role=UserRole.GESTOR,
                status=UserStatus.ACTIVE,
                matricula="GESTOR-CG-001",
                salario=12000.00,
            )
            db.session.add(manager)

            # 3. Bus
            print("3. Creating Bus...")
            bus = Onibus(
                id=ID_BUS_CG,
                prefeitura_id=ID_PREF_CG,
                placa="CGP2024",
                modelo="Marcopolo Paradiso 1200",
                capacidade=45,
            )
            db.session.add(bus)

            # 4. Driver
            print("4. Creating Driver (tiao@buska.app)...")
            driver = Motorista(
                id=ID_DRIVER_CG,
                prefeitura_id=ID_PREF_CG,
                nome="Sebastião Silva",
                email="tiao@buska.app",
                senha_hash=secure_password,
                cpf="22222222223",
                telefone="83999990002",
                role=UserRole.MOTORISTA,
                status=UserStatus.ACTIVE,
                cnh="12345678902",
            )
            db.session.add(driver)
            db.session.flush()

            # 5. Route Stops (Galante)
            print("5. Creating Route Stops (Galante)...")
            galante_stops_data = [
                ("Tapera Lanches", -7.313400427823559, -35.77219830053171),
                ("Pizzaria de Zelito", -7.305464604985933, -35.77920716806884),
                ("Hospital Galante", -7.305990, -35.785673),
            ]
            boarding_stops = []
            for name, lat, lon in galante_stops_data:
                stop = Ponto(prefeitura_id=ID_PREF_CG, latitude=lat, longitude=lon, apelido=name)
                db.session.add(stop)
                boarding_stops.append(stop)
            db.session.flush()

            # 6. Institutions (Campina Grande)
            print("6. Creating Institutions (Campina Grande)...")
            institutions_data = [
                (
                    "IFPB Campina Grande",
                    -7.240062929884356,
                    -35.91617862179549,
                    TipoInstituicao.INSTITUTO_FEDERAL,
                ),
                (
                    "UNIFIP - Campus CG",
                    -7.235530802182051,
                    -35.916702975751285,
                    TipoInstituicao.UNIVERSIDADE_PRIVADA,
                ),
                (
                    "UEPB",
                    -7.208916684618096,
                    -35.91726583157035,
                    TipoInstituicao.UNIVERSIDADE_PUBLICA,
                ),
                ("IEPB", -7.219132730074228, -35.881355089242774, TipoInstituicao.ESCOLA_PRIVADA),
                (
                    "Colégio SÃO VICENTE",
                    -7.218499173020027,
                    -35.8809411641136,
                    TipoInstituicao.ESCOLA_PRIVADA,
                ),
                (
                    "Colégio 11 DE OUTUBRO",
                    -7.220521217773388,
                    -35.87939089109635,
                    TipoInstituicao.ESCOLA_PRIVADA,
                ),
                (
                    "UNINASSAU",
                    -7.230214404724237,
                    -35.88665471807876,
                    TipoInstituicao.UNIVERSIDADE_PRIVADA,
                ),
                (
                    "Colégio Rebouças",
                    -7.228522577966405,
                    -35.880458077604835,
                    TipoInstituicao.ESCOLA_PRIVADA,
                ),
            ]

            institution_stops = []
            institutions = []
            for name, lat, lon, inst_type in institutions_data:
                stop = Ponto(prefeitura_id=ID_PREF_CG, latitude=lat, longitude=lon, apelido=name)
                db.session.add(stop)
                db.session.flush()
                institution_stops.append(stop)

                inst = Instituicao(nome=name, tipo=inst_type, ponto_id=stop.id)
                db.session.add(inst)
                institutions.append(inst)
            db.session.flush()

            # 7. Students
            print("7. Creating Students...")
            students = []
            for i in range(1, 16):
                home_stop = random.choice(boarding_stops)
                student = Aluno(
                    prefeitura_id=ID_PREF_CG,
                    nome=f"Estudante de Galante {i}",
                    email=f"alunocg{i}@buska.app",
                    senha_hash=secure_password,
                    cpf=f"444444444{i:02d}",
                    matricula=f"MATCG{i:04d}",
                    role=UserRole.ALUNO,
                    status=UserStatus.ACTIVE,
                    instituicao_id=random.choice(institutions).id,
                    ponto_casa_id=home_stop.id,
                )
                db.session.add(student)
                students.append(student)
            db.session.flush()

            # 8. Route
            print("8. Creating Route...")
            route = Rota(
                id=ID_ROUTE_CG,
                prefeitura_id=ID_PREF_CG,
                nome="Expresso Galante -> Campina Grande",
                motorista_padrao_id=ID_DRIVER_CG,
                veiculo_padrao_id=ID_BUS_CG,
            )
            db.session.add(route)
            db.session.flush()

            # Route Stops Mapping
            order = 1
            route_points = []
            for p in boarding_stops:
                rp = RotaPonto(rota_id=route.id, ponto_id=p.id, ordem=order)
                db.session.add(rp)
                route_points.append(rp)
                order += 1
            for p in institution_stops:
                rp = RotaPonto(rota_id=route.id, ponto_id=p.id, ordem=order)
                db.session.add(rp)
                route_points.append(rp)
                order += 1
            db.session.flush()

            # 9. Schedules & Subscriptions
            print("9. Creating Schedules and Subscriptions...")
            schedules_data = [
                (time(8, 0), SentidoViagem.IDA),
                (time(12, 0), SentidoViagem.CIRCULAR),
                (time(13, 0), SentidoViagem.CIRCULAR),
                (time(18, 0), SentidoViagem.VOLTA),
            ]

            schedules = []
            for departure_time, direction in schedules_data:
                schedule = HorarioRota(
                    rota_id=route.id, horario_saida=departure_time, sentido=direction
                )
                db.session.add(schedule)
                db.session.flush()
                schedules.append((schedule, direction))

                # Running Monday to Friday
                for day in [
                    DiaDaSemana.SEG,
                    DiaDaSemana.TER,
                    DiaDaSemana.QUA,
                    DiaDaSemana.QUI,
                    DiaDaSemana.SEX,
                ]:
                    db.session.add(DiasOperacao(horario_rota_id=schedule.id, dia=day))

            for s in students:
                db.session.add(RotaAluno(rota_id=route.id, aluno_id=s.usuario_id))
            db.session.flush()

            # 10. Trips and Telemetry
            print("10. Generating Historical, Present, and Future Trips...")
            now = datetime.now(UTC)
            today = now.date()

            for schedule, direction in schedules:
                # --------------------------------------------------
                # A. PAST TRIPS (Last 4 days)
                # --------------------------------------------------
                for d in range(1, 5):
                    trip_date = today - timedelta(days=d)

                    if trip_date.weekday() >= 5:  # Skip weekends
                        continue

                    start_time = datetime.combine(trip_date, schedule.horario_saida).replace(
                        tzinfo=UTC
                    )

                    trip = Viagem(
                        data=trip_date,
                        horario_rota_id=schedule.id,
                        motorista_id=route.motorista_padrao_id,
                        veiculo_id=route.veiculo_padrao_id,
                        status=StatusViagem.FINALIZADA,
                        inicio_real=start_time,
                        fim_real=start_time + timedelta(minutes=50),
                        km_real=random.uniform(22.0, 26.0),
                    )
                    db.session.add(trip)
                    db.session.flush()

                    for rp in route_points:
                        db.session.add(
                            ViagemPonto(
                                viagem_id=trip.id,
                                ponto_id=rp.ponto_id,
                                ordem=rp.ordem,
                                visitado=True,
                                chegada_real=start_time + timedelta(minutes=rp.ordem * 4),
                            )
                        )

                    for student in students:
                        confirmed = random.choice([True, True, False])
                        db.session.add(
                            AlunosConfirmados(
                                viagem_id=trip.id,
                                aluno_id=student.usuario_id,
                                confirmacao=confirmed,
                                ponto_embarque_id=boarding_stops[0].id if confirmed else None,
                                embarcou=confirmed and random.choice([True, True, False]),
                            )
                        )

                    # Telemetry Simulation
                    start_lat, start_lon = float(boarding_stops[0].latitude), float(
                        boarding_stops[0].longitude
                    )
                    end_lat, end_lon = float(institution_stops[2].latitude), float(
                        institution_stops[2].longitude
                    )

                    if direction == SentidoViagem.VOLTA:
                        start_lat, start_lon, end_lat, end_lon = (
                            end_lat,
                            end_lon,
                            start_lat,
                            start_lon,
                        )

                    gps_coords = interpolate_coordinates(
                        (start_lat, start_lon), (end_lat, end_lon), 10
                    )

                    for idx, coord in enumerate(gps_coords):
                        db.session.add(
                            TelemetriaViagem(
                                viagem_id=trip.id,
                                latitude=coord[0],
                                longitude=coord[1],
                                timestamp=start_time + timedelta(minutes=idx * 5),
                            )
                        )

                # --------------------------------------------------
                # B. TODAY'S TRIPS
                # --------------------------------------------------
                if today.weekday() < 5:
                    status_today = (
                        StatusViagem.FINALIZADA
                        if schedule.horario_saida < now.time()
                        else StatusViagem.AGENDADA
                    )

                    trip_today = Viagem(
                        data=today,
                        horario_rota_id=schedule.id,
                        motorista_id=route.motorista_padrao_id,
                        veiculo_id=route.veiculo_padrao_id,
                        status=status_today,
                        inicio_real=(
                            now - timedelta(minutes=20)
                            if status_today == StatusViagem.FINALIZADA
                            else None
                        ),
                    )
                    db.session.add(trip_today)
                    db.session.flush()

                    for rp in route_points:
                        db.session.add(
                            ViagemPonto(
                                viagem_id=trip_today.id,
                                ponto_id=rp.ponto_id,
                                ordem=rp.ordem,
                                visitado=(status_today == StatusViagem.FINALIZADA),
                            )
                        )

                    for student in students:
                        db.session.add(
                            AlunosConfirmados(
                                viagem_id=trip_today.id,
                                aluno_id=student.usuario_id,
                                confirmacao=random.choice([True, False]),
                                ponto_embarque_id=boarding_stops[0].id,
                                embarcou=False,
                            )
                        )

                # --------------------------------------------------
                # C. FUTURE TRIPS (Next 14 days)
                # --------------------------------------------------
                for d in range(1, 15):
                    future_date = today + timedelta(days=d)

                    if future_date.weekday() >= 5:  # Skip weekends
                        continue

                    future_trip = Viagem(
                        data=future_date,
                        horario_rota_id=schedule.id,
                        motorista_id=route.motorista_padrao_id,
                        veiculo_id=route.veiculo_padrao_id,
                        status=StatusViagem.AGENDADA,
                    )
                    db.session.add(future_trip)
                    db.session.flush()

                    # Future points (not visited yet)
                    for rp in route_points:
                        db.session.add(
                            ViagemPonto(
                                viagem_id=future_trip.id,
                                ponto_id=rp.ponto_id,
                                ordem=rp.ordem,
                                visitado=False,
                            )
                        )

                    # Future students (simulating early confirmers)
                    for student in students:
                        confirmed = random.choice(
                            [True, False, False, False]
                        )  # Most haven't confirmed yet
                        db.session.add(
                            AlunosConfirmados(
                                viagem_id=future_trip.id,
                                aluno_id=student.usuario_id,
                                confirmacao=confirmed,
                                ponto_embarque_id=boarding_stops[0].id if confirmed else None,
                                embarcou=False,
                            )
                        )

            db.session.commit()

            print("\n" + "=" * 50)
            print("SUCCESS! Database populated with Campina Grande data.")
            print("=" * 50)
            print("\nTest Users (password: 123456):")
            print("  Gestor:    gestor.cg@buska.app")
            print("  Motorista: tiao@buska.app")
            print("  Aluno:     alunocg1@buska.app\n")

        except Exception as e:
            db.session.rollback()
            print(f"Error: {e}")
            raise


if __name__ == "__main__":
    seed_database()
