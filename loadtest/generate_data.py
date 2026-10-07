"""
BusKá Load Test — tier-parametrized data generator.

Extends the patterns in seed.py (same models, same joined-table user
inheritance, same TEST_PASSWORD convention) but:
  - is fully self-contained: creates its own Prefeitura rows instead of
    depending on a pre-imported IBGE municipality CSV catalog, so it works
    against a bare, freshly-migrated database.
  - is driven by a tier JSON config (see loadtest/tiers/*.json) describing
    one or more municípios, each with a target bus/route count and student
    count, so the exact same script produces the Smoke, Baseline, Load,
    Capacity, Stress, and Breakpoint tiers by swapping the config file.
  - uses bulk Core inserts (not one-object-at-a-time ORM adds) for the
    high-volume entities (alunos, pontos, enrollments, confirmations) so it
    can realistically reach the Breakpoint tier's ~99k students without
    taking hours.
  - is idempotent per tier: re-running with the same config wipes and
    regenerates only the prefeituras listed in that config (matched by
    codigo_ibge), so tiers can be layered/re-run without a full DB reset.

Usage:
    python loadtest/generate_data.py --tier loadtest/tiers/baseline.json
    python loadtest/generate_data.py --tier loadtest/tiers/baseline.json --export loadtest/exports/baseline_export.json

Requires the same environment variables as the app itself (DB_HOST, DB_USER,
etc.) — run it from inside the API container or with the same env loaded,
e.g.:
    docker compose -f docker-compose.loadtest.yml exec api \\
        python loadtest/generate_data.py --tier loadtest/tiers/baseline.json --export loadtest/exports/baseline_export.json
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
import uuid
from datetime import UTC, date, datetime, time as dtime, timedelta
from pathlib import Path

from sqlalchemy import delete, insert, select
from werkzeug.security import generate_password_hash

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app  # noqa: E402
from app.models.base import db  # noqa: E402
from app.models.enum import (  # noqa: E402
    SentidoViagem,
    StatusViagem,
    TipoInstituicao,
    UserRole,
    UserStatus,
)
from app.models.geo import Instituicao, Ponto  # noqa: E402
from app.models.onibus import Onibus  # noqa: E402
from app.models.prefeitura import Prefeitura  # noqa: E402
from app.models.rota import HorarioRota, Rota, RotaAluno, RotaPonto  # noqa: E402
from app.models.user import Aluno, Gestor, Motorista  # noqa: E402
from app.models.viagem import AlunosConfirmados, Viagem, ViagemPonto  # noqa: E402

TEST_PASSWORD = "buska123"
BUS_MODELS = [
    ("Mercedes-Benz Sprinter 515", 30),
    ("Volare W9 Escolar", 44),
    ("Volkswagen 15.190 EOD", 35),
    ("Marcopolo Viale", 40),
    ("Iveco CityClass Escolar", 38),
    ("Agrale MT 12.0", 32),
    ("Volare A8 Escolar", 45),
    ("Mercedes-Benz Of-1721", 29),
]
BATCH_SIZE = 2000


def slugify(text: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in text).strip("-")


def load_tier_config(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_or_create_prefeitura(spec: dict) -> Prefeitura:
    pref = db.session.query(Prefeitura).filter_by(codigo_ibge=spec["codigo_ibge"]).first()
    if pref:
        return pref
    pref = Prefeitura(
        id=uuid.uuid4(),
        nome=spec["nome"],
        estado=spec["estado"],
        codigo_ibge=spec["codigo_ibge"],
        ativo=True,
    )
    db.session.add(pref)
    db.session.flush()
    return pref


def wipe_prefeitura_data(pref_id) -> None:
    """Delete any previously generated load-test data for this município.

    Order matters here because several FKs are RESTRICT/NO ACTION rather
    than CASCADE (Aluno.instituicao_id, Aluno.ponto_casa_id,
    AlunosConfirmados.ponto_embarque_id/ponto_destino_id, Viagem.veiculo_id,
    Viagem.motorista_id all have no ON DELETE rule, i.e. RESTRICT). Deleting
    in the wrong order raises a FK violation instead of silently cascading:

      1. viagem (matched via its buses) -> cascades viagem_ponto,
         alunos_confirmados (both ON DELETE CASCADE on viagem_id).
      2. usuario (aluno/motorista/gestor subtype rows cascade via their PK
         FK ON DELETE CASCADE) -> also cascades rota_aluno.
      3. rota -> cascades horario_rota, rota_ponto.
      4. onibus, instituicao, ponto — now nothing left referencing them.
    """
    from app.models.user import User

    db.session.execute(
        delete(Viagem).where(
            Viagem.veiculo_id.in_(select(Onibus.id).where(Onibus.prefeitura_id == pref_id))
        )
    )
    db.session.execute(delete(User).where(User.prefeitura_id == pref_id))
    db.session.execute(delete(Rota).where(Rota.prefeitura_id == pref_id))
    db.session.execute(delete(Onibus).where(Onibus.prefeitura_id == pref_id))
    db.session.execute(delete(Instituicao).where(Instituicao.prefeitura_id == pref_id))
    db.session.execute(delete(Ponto).where(Ponto.prefeitura_id == pref_id))
    db.session.commit()


def jitter_point(
    center_lat: float, center_lon: float, radius_deg: float = 0.04
) -> tuple[float, float]:
    lat = center_lat + random.uniform(-radius_deg, radius_deg)
    lon = center_lon + random.uniform(-radius_deg, radius_deg)
    return round(lat, 8), round(lon, 8)


def bulk_insert_pontos(pref_id, points: list[tuple[float, float, str]]) -> list[uuid.UUID]:
    """points: list of (lat, lon, apelido). Returns generated ids in order."""
    rows = []
    ids = []
    for lat, lon, apelido in points:
        pid = uuid.uuid4()
        ids.append(pid)
        rows.append(
            {
                "id": pid,
                "prefeitura_id": pref_id,
                "latitude": lat,
                "longitude": lon,
                "apelido": apelido,
            }
        )
    if rows:
        db.session.execute(insert(Ponto.__table__), rows)
    return ids


def generate_prefeitura(
    spec: dict, pw_hash: str, today: date, stats: dict, tier_name: str, tier_seed: int
) -> dict:
    """Generates one município's worth of fleet/routes/students. Returns an
    export dict of credentials + ids for the k6 side."""
    codigo_ibge = spec["codigo_ibge"]
    nome = spec["nome"]
    num_buses = spec["buses"]
    num_students = spec["students"]
    center_lat, center_lon = spec["center_lat"], spec["center_lon"]
    slug = slugify(nome)[:20]

    print(f"\n--- {nome} (IBGE {codigo_ibge}): {num_buses} buses, {num_students} students ---")

    # Re-seed per-município (not just once globally in main()) so every
    # município gets its own deterministic-but-distinct random stream. With
    # only a single global seed, two different tiers' first prefeitura would
    # draw the exact same "random" CPF/CNH sequence — harmless in isolation,
    # but wipe_prefeitura_data() only clears rows for the current
    # codigo_ibge, so previously generated tiers' municípios are still in the
    # DB and a collision throws usuario_cpf_key. Salting with codigo_ibge
    # keeps runs fully reproducible while making every município's stream
    # independent of which other tiers have already been generated.
    random.seed(f"{tier_seed}:{codigo_ibge}")

    pref = get_or_create_prefeitura(spec)
    wipe_prefeitura_data(pref.id)

    # ── Gestor ────────────────────────────────────────────────────────────
    gestor_email = f"loadtest-{slug}-gestor@buska.app"
    gestor = Gestor(
        id=uuid.uuid4(),
        prefeitura_id=pref.id,
        nome=f"Gestor(a) Loadtest {nome}",
        email=gestor_email,
        senha_hash=pw_hash,
        cpf=f"{random.randint(10**10, 10**11 - 1)}",
        telefone="83999990000",
        role=UserRole.GESTOR,
        status=UserStatus.ACTIVE,
    )
    db.session.add(gestor)
    db.session.flush()

    # ── Instituições (2 per município: 1 school, 1 university) ─────────────
    inst_lat1, inst_lon1 = jitter_point(center_lat, center_lon, 0.01)
    inst_lat2, inst_lon2 = jitter_point(center_lat, center_lon, 0.01)
    [inst_ponto1_id, inst_ponto2_id] = bulk_insert_pontos(
        pref.id,
        [
            (inst_lat1, inst_lon1, f"Escola Municipal — {nome}"),
            (inst_lat2, inst_lon2, f"Campus Universitário — {nome}"),
        ],
    )
    inst1 = Instituicao(
        id=uuid.uuid4(),
        nome=f"Escola Municipal de {nome}",
        tipo=TipoInstituicao.ESCOLA_PUBLICA,
        fonte="LOADTEST",
        codigo_externo=f"{codigo_ibge}-ESC",
        uf=spec["estado"],
        prefeitura_id=pref.id,
        ponto_id=inst_ponto1_id,
        situacao="ATIVA",
        categoria_administrativa="Pública",
    )
    inst2 = Instituicao(
        id=uuid.uuid4(),
        nome=f"Campus Universitário de {nome}",
        tipo=TipoInstituicao.UNIVERSIDADE_PUBLICA,
        fonte="LOADTEST",
        codigo_externo=f"{codigo_ibge}-UNI",
        uf=spec["estado"],
        prefeitura_id=pref.id,
        ponto_id=inst_ponto2_id,
        situacao="ATIVA",
        categoria_administrativa="Pública",
    )
    db.session.add_all([inst1, inst2])
    db.session.flush()
    instituicao_ids = [inst1.id, inst2.id]

    # ── Frota (buses) ────────────────────────────────────────────────────
    buses = []
    for i in range(num_buses):
        modelo, capacidade = BUS_MODELS[i % len(BUS_MODELS)]
        placa = f"{spec['estado']}{slug[:2].upper()}{i:04d}".replace(" ", "")[:10]
        bus = Onibus(
            id=uuid.uuid4(),
            prefeitura_id=pref.id,
            placa=placa,
            modelo=modelo,
            capacidade=capacidade,
        )
        db.session.add(bus)
        buses.append(bus)
    db.session.flush()

    # ── Motoristas (1 per bus) ───────────────────────────────────────────
    motoristas = []
    for i in range(num_buses):
        mot = Motorista(
            id=uuid.uuid4(),
            prefeitura_id=pref.id,
            nome=f"Motorista Loadtest {i + 1} — {nome}",
            email=f"loadtest-{slug}-mot{i + 1}@buska.app",
            senha_hash=pw_hash,
            cpf=f"{random.randint(10**10, 10**11 - 1)}",
            telefone="83999880000",
            role=UserRole.MOTORISTA,
            status=UserStatus.ACTIVE,
            cnh=f"{random.randint(10**10, 10**11 - 1)}",
        )
        db.session.add(mot)
        motoristas.append(mot)
    db.session.flush()

    # ── Route stop points (shared pool, reused by nearby routes) ─────────
    n_stop_points = max(4, num_buses * 2)
    stop_points_raw = [
        (*jitter_point(center_lat, center_lon), f"Parada {i + 1} — {nome}")
        for i in range(n_stop_points)
    ]
    stop_point_ids = bulk_insert_pontos(pref.id, stop_points_raw)

    # ── Rotas (1 per bus): each gets 3 stop points + the school/uni as last stop ──
    rotas = []
    horarios = []
    saida_base = dtime(5, 30)
    for i in range(num_buses):
        rota = Rota(
            id=uuid.uuid4(),
            prefeitura_id=pref.id,
            nome=f"Rota {i + 1} — {nome} (Manhã)",
            motorista_padrao_id=motoristas[i].id,
            veiculo_padrao_id=buses[i].id,
        )
        db.session.add(rota)
        db.session.flush()

        pontos_da_rota = [stop_point_ids[(i * 3 + j) % len(stop_point_ids)] for j in range(3)] + [
            inst_ponto1_id if i % 2 == 0 else inst_ponto2_id
        ]
        for ordem, ponto_id in enumerate(pontos_da_rota, 1):
            db.session.add(RotaPonto(rota_id=rota.id, ponto_id=ponto_id, ordem=ordem))

        # spread departure times across the morning rush (05:00-07:00) like real school runs
        minute_offset = (i * 7) % 120
        h, m = divmod(saida_base.hour * 60 + saida_base.minute + minute_offset, 60)
        horario = HorarioRota(
            id=uuid.uuid4(),
            rota_id=rota.id,
            horario_saida=dtime(h % 24, m),
            sentido=SentidoViagem.IDA,
        )
        db.session.add(horario)

        rotas.append((rota, pontos_da_rota))
        horarios.append(horario)

    db.session.flush()

    # ── Viagens EM_ANDAMENTO (today, one per route) + their ViagemPonto rows ──
    viagens = []
    viagem_ponto_rows = []
    for (rota, pontos_da_rota), horario, motorista, bus in zip(
        rotas, horarios, motoristas, buses, strict=True
    ):
        viagem = Viagem(
            id=uuid.uuid4(),
            data=today,
            horario_rota_id=horario.id,
            motorista_id=motorista.id,
            veiculo_id=bus.id,
            status=StatusViagem.EM_ANDAMENTO,
            inicio_real=datetime.now(UTC),
        )
        db.session.add(viagem)
        db.session.flush()
        for ordem, ponto_id in enumerate(pontos_da_rota, 1):
            viagem_ponto_rows.append(
                {"viagem_id": viagem.id, "ponto_id": ponto_id, "ordem": ordem, "visitado": False}
            )
        viagens.append((viagem, rota, pontos_da_rota))

    if viagem_ponto_rows:
        db.session.execute(insert(ViagemPonto.__table__), viagem_ponto_rows)
    db.session.commit()

    # ── Alunos (bulk insert into usuario + aluno) ─────────────────────────
    home_points_raw = [
        (*jitter_point(center_lat, center_lon), f"Res. Aluno {i + 1} — {nome}")
        for i in range(num_students)
    ]
    home_point_ids = bulk_insert_pontos(pref.id, home_points_raw)
    db.session.commit()

    usuario_rows = []
    aluno_rows = []
    aluno_ids = []
    aluno_emails = []
    adult_birth_range = (date(1998, 1, 1), date(2005, 12, 31))

    now = datetime.now(UTC)
    for i in range(num_students):
        uid = uuid.uuid4()
        aluno_ids.append(uid)
        email = f"loadtest-{slug}-aluno{i + 1}@buska.app"
        aluno_emails.append(email)
        usuario_rows.append(
            {
                "id": uid,
                "prefeitura_id": pref.id,
                "nome": f"Aluno Loadtest {i + 1} — {nome}",
                "email": email,
                "senha_hash": pw_hash,
                "telefone": "83988010000",
                "cpf": f"{codigo_ibge}{i:05d}"[:14],
                "receber_notificacoes": True,
                "role": UserRole.ALUNO,
                "status": UserStatus.ACTIVE,
                "created_at": now,
                "updated_at": now,
            }
        )
        days_offset = random.randint(0, (adult_birth_range[1] - adult_birth_range[0]).days)
        aluno_rows.append(
            {
                "usuario_id": uid,
                "matricula": f"{codigo_ibge}-{i + 1:06d}",
                "instituicao_id": instituicao_ids[i % 2],
                "ponto_casa_id": home_point_ids[i],
                "data_nascimento": adult_birth_range[0] + timedelta(days=days_offset),
            }
        )

    from app.models.user import User

    t0 = time.time()
    for start in range(0, len(usuario_rows), BATCH_SIZE):
        db.session.execute(insert(User.__table__), usuario_rows[start : start + BATCH_SIZE])
        db.session.execute(insert(Aluno.__table__), aluno_rows[start : start + BATCH_SIZE])
        db.session.commit()
        print(
            f"    ...{min(start + BATCH_SIZE, len(usuario_rows))}/{len(usuario_rows)} alunos",
            end="\r",
        )
    if usuario_rows:
        print()
    print(f"    alunos inserted in {time.time() - t0:.1f}s")

    # ── Enroll students round-robin across routes + confirm on today's trip ──
    rota_aluno_rows = []
    confirmacao_rows = []
    n_rotas = len(rotas)
    for i, aluno_id in enumerate(aluno_ids):
        rota_idx = i % n_rotas
        rota, pontos_da_rota = rotas[rota_idx]
        viagem, _, _ = viagens[rota_idx]
        rota_aluno_rows.append({"rota_id": rota.id, "aluno_id": aluno_id, "data_inscricao": now})
        confirmacao_rows.append(
            {
                "viagem_id": viagem.id,
                "aluno_id": aluno_id,
                "confirmacao": True,
                "ponto_embarque_id": pontos_da_rota[0],
                "ponto_destino_id": pontos_da_rota[-1],
                "embarcou": False,
                "tentativas_auto_checkin": 0,
            }
        )

    for start in range(0, len(rota_aluno_rows), BATCH_SIZE):
        db.session.execute(insert(RotaAluno.__table__), rota_aluno_rows[start : start + BATCH_SIZE])
        db.session.execute(
            insert(AlunosConfirmados.__table__), confirmacao_rows[start : start + BATCH_SIZE]
        )
        db.session.commit()

    stats["prefeituras"] += 1
    stats["buses"] += num_buses
    stats["students"] += num_students
    stats["trips"] += len(viagens)

    return {
        "codigo_ibge": codigo_ibge,
        "nome": nome,
        "gestor": {"email": gestor_email, "password": TEST_PASSWORD},
        "motoristas": [
            {"email": m.email, "password": TEST_PASSWORD, "viagem_id": str(v[0].id)}
            for m, v in zip(motoristas, viagens, strict=True)
        ],
        "alunos": [
            {
                "email": email,
                "password": TEST_PASSWORD,
                "viagem_id": str(viagens[i % n_rotas][0].id),
            }
            for i, email in enumerate(aluno_emails)
        ],
        "rotas": [str(r.id) for r, _ in rotas],
        "viagens_em_andamento": [str(v.id) for v, _, _ in viagens],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="BusKá load-test data generator")
    parser.add_argument("--tier", required=True, help="Path to a tiers/<name>.json config")
    parser.add_argument("--export", help="Path to write the credentials/ids export JSON for k6")
    parser.add_argument("--seed", type=int, default=None, help="Override the config's random seed")
    args = parser.parse_args()

    config_path = Path(args.tier)
    config = load_tier_config(config_path)
    seed = args.seed if args.seed is not None else config.get("seed", 42)
    random.seed(seed)

    app = create_app()
    with app.app_context():
        print("=" * 60)
        print(f"BusKá Load Test — generating tier: {config['tier']} ({config.get('label', '')})")
        print(f"Random seed: {seed}")
        print("=" * 60)

        pw_hash = generate_password_hash(TEST_PASSWORD)
        today = date.today()
        stats = {"prefeituras": 0, "buses": 0, "students": 0, "trips": 0}

        export = {
            "tier": config["tier"],
            "label": config.get("label", ""),
            "generated_at": datetime.now(UTC).isoformat(),
            "base_url": config.get("base_url", "http://localhost:5000"),
            "prefeituras": [],
        }

        t_start = time.time()
        for spec in config["prefeituras"]:
            pref_export = generate_prefeitura(spec, pw_hash, today, stats, config["tier"], seed)
            export["prefeituras"].append(pref_export)

        elapsed = time.time() - t_start
        print("\n" + "=" * 60)
        print(
            f"Done in {elapsed:.1f}s: {stats['prefeituras']} prefeituras, "
            f"{stats['buses']} buses/routes, {stats['trips']} active trips, "
            f"{stats['students']} students."
        )
        print("=" * 60)

        export_path = (
            Path(args.export)
            if args.export
            else (Path(__file__).parent / "exports" / f"{config['tier']}_export.json")
        )
        export_path.parent.mkdir(parents=True, exist_ok=True)
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(export, f, indent=2, ensure_ascii=False)
        print(f"Export written to {export_path}")


if __name__ == "__main__":
    main()
