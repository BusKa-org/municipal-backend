# BusKá Load Test Suite

Implements the tiered load test plan (Smoke → Baseline → Load → Capacity →
Stress → Breakpoint). See the plan document for the full rationale, sourcing
of every number, and the go/no-go gates between tiers. This README covers
how to actually run it.

**Results so far:** see [`REPORT.md`](REPORT.md) for the wrap-up of Smoke,
Baseline, and Load (+ Spike/Soak variants) — including the confirmed
Gunicorn-concurrency bottleneck, the "Dawn Departure" spike finding, and
infra recommendations. Capacity/Stress/Breakpoint are documented there as
deferred (need a second VM).

**Why it is built this way:**
[`docs/adr/0001-tiered-load-testing-harness.md`](../docs/adr/0001-tiered-load-testing-harness.md)
records the design decisions, the alternatives rejected, and the open
questions still up for comment.

## 1. One-time setup

```bash
cd buska-backend
uv sync                 # or: pip install -e .
brew install k6          # or see https://k6.io/docs/get-started/installation/
```

## 2. Start the isolated environment

Never point any of this at `docker-compose.prod.yml` / the production VM.

```bash
docker compose -f docker-compose.loadtest.yml up -d --build db osrm-stub
DB_HOST=localhost uv run alembic upgrade head   # run migrations from the host, against the exposed db port
docker compose -f docker-compose.loadtest.yml up -d --build api
curl http://localhost:5000/health
```

This brings up:
- `db` — Postgres/PostGIS, resource-limited to 2 vCPU / 4GB (half the prod VM
  spec, leaving the other half for `api`, matching how they'd actually share
  the single prod host).
- `api` — the Flask app, same limits, `OSRM_BASE_URL` pointed at the local
  stub, dummy Firebase/Mail config.
- `osrm-stub` — a ~150-line stdlib Python server returning synthetic
  straight-line polylines (see `osrm-stub/server.py`) so no load test traffic
  ever reaches the public `router.project-osrm.org` demo server.

Tear down and wipe data between tiers with:

```bash
docker compose -f docker-compose.loadtest.yml down -v
```

## 3. Run a tier

```bash
./loadtest/run_tier.sh smoke
./loadtest/run_tier.sh baseline
./loadtest/run_tier.sh load
./loadtest/run_tier.sh load-spike  --data-source load   # reuses load's dataset
./loadtest/run_tier.sh load-soak   --data-source load   # edit tiers/load-soak.json to extend past the 4h default
./loadtest/run_tier.sh capacity     # needs the second VM, see below
./loadtest/run_tier.sh stress       # needs the second VM
./loadtest/run_tier.sh breakpoint   # needs the second VM
```

Each run: generates/refreshes that tier's data (`generate_data.py`), checks
`/health`, starts `observe.sh` (docker stats + Postgres slow-query log +
Gunicorn logs), runs the full k6 scenario mix, stops observability, and
writes everything to `results/<tier>-<timestamp>/`.

Routing proxy and batch trip generation are excluded from the default mix
(per the plan, they're isolated/burst scenarios) — add them with:

```bash
./loadtest/run_tier.sh load --extra routing_proxy,batch_trip_generation
```

Smoke and Baseline are also promoted into a manual CI check —
[`.github/workflows/loadtest-regression.yml`](../.github/workflows/loadtest-regression.yml),
run via the Actions tab's "Run workflow" button (`workflow_dispatch`).

## 4. Capacity / Stress / Breakpoint need a second host

Local Docker Compose on one machine is not representative once you're
modeling multiple concurrent municípios and tens of thousands of students —
see the plan's "Isolated test environment" section. Those three tiers need:
- A second OpenStack VM (or equivalent) of the same `general.large` flavor
  (or larger, if intentionally probing past current capacity) running
  `docker-compose.loadtest.yml`.
- `k6` run from a **third**, separate host (or at minimum a separate VM from
  the one under test) so the load generator itself never steals CPU from the
  system under test.
- Point `run_tier.sh` at the remote target: `BASE_URL=http://<vm-ip>:5000 ./loadtest/run_tier.sh capacity`.

## Repo layout

```
loadtest/
  generate_data.py       # tier-parametrized data generator (extends seed.py's patterns)
  run_tier.sh             # orchestrates one full tier run end-to-end
  observe.sh              # docker stats + pg slow-query + gunicorn log capture
  tiers/                  # one JSON config per tier: sizing + k6 ramp shape
  exports/                # generate_data.py output: credentials/ids for k6 (gitignored)
  k6/
    main.js               # builds the weighted scenario mix from a tier's sizing numbers
    lib/                  # config.js (data loading), auth.js (token cache), thresholds.js
    scenarios/            # one file per user action, matches the plan's k6 scenario design
  osrm-stub/              # stdlib Python OSRM-compatible stub server
  results/                # k6 + observability output per run (gitignored)
```

## Notes / deliberate deviations from a literal reading of the plan

- **Student browsing** uses `GET /v1/viagens/aluno/agenda` instead of a
  generic `GET /v1/viagens` — the latter is gestor-only
  (`list_viagens_gestor` rejects non-`GESTOR` roles), so a student session
  hitting it would just be a wall of 403s, not real traffic.
- **Capacity/Stress "N towns at the same profile"** are generated as
  synthetic clones of the one real, sourced município at that scale
  (`codigo_ibge` prefixes `9500xxxx`/`9600xxxx`, which aren't used by any
  real Brazilian state) — see the `source_note` field on each entry in
  `tiers/capacity.json` / `tiers/stress.json`. This is an explicit modeling
  choice, not a claim that N distinct real towns were independently sourced.
