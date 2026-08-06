# AGENTS.md

Instructions for AI coding agents working in this repository. Read this first;
follow links for anything deeper rather than expecting it duplicated here.

## What this is

BusKá backend: a Flask API managing routes, trips, students, drivers and
vehicles for municipal school transport. Multi-tenant by `Prefeitura`
(municipality). Full architecture, layering, and domain model:
[`docs/architecture.md`](docs/architecture.md).

Stack: Flask + Flask-RESTX, PostgreSQL + PostGIS, SQLAlchemy + GeoAlchemy2,
Marshmallow, Flask-JWT-Extended, `uv` as the package manager.

## Running things

```bash
make install        # install dependencies (uv)
make run             # run the dev server, port 5000
make initdb          # create + seed the database
uv run pytest -m "not e2e" -q   # unit + integration tests (what pre-commit runs)
uv run pytest -m e2e            # e2e tests, needs the full stack up
pre-commit run --all-files      # lint + format + test, same as CI
```

Integration and e2e tests need Postgres/PostGIS reachable
(`docker compose -f infra/database.yml up -d`, or `make run` if already
configured). If `pytest` fails in pre-commit with a connection error, that is
almost always a missing local database, not a code problem.

Full local setup options: [`README.md`](README.md).

## Conventions that are enforced, not just suggested

- **Commit messages and PR titles must be Conventional Commits**
  (`feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert: ...`,
  header ≤ 100 chars). Enforced by the `conventional-pre-commit` hook locally
  and by `commitlint`/`action-semantic-pull-request` in CI. A commit that
  violates this will be rejected before it reaches GitHub.
- **Pre-commit runs on every commit**: `black`, `ruff --fix`, `mypy`
  (excludes `migrations/` and `tests/`), and `pytest -m "not e2e"`. Don't
  disable or skip a hook to get a commit through; fix what it flagged.
- **Service layer owns business logic and authorization checks.** Controllers
  parse/validate/serialize only; models are data structure only. See
  "Architecture Pattern" in [`docs/architecture.md`](docs/architecture.md).
- **Raise typed exceptions from `app/core/exceptions.py`**
  (`NotFoundError`, `ValidationError`, `ForbiddenError`, `UnauthorizedError`,
  `ConflictError`), not raw `Exception` or a bare error dict — the global
  handlers map these to the right HTTP status.

## Where to look for more

| Question | Look here |
|---|---|
| How is the app structured / layered? | [`docs/architecture.md`](docs/architecture.md) |
| Why was a non-obvious decision made? | [`docs/adr/`](docs/adr/) — check the index before assuming something is undocumented |
| What does an endpoint accept/return? | [`docs/api_contracts.md`](docs/api_contracts.md), [`docs/endpoints/`](docs/endpoints/), or the running Swagger UI at `/docs` |
| How does the load-testing harness work? | [`docs/adr/0001-tiered-load-testing-harness.md`](docs/adr/0001-tiered-load-testing-harness.md), [`loadtest/README.md`](loadtest/README.md) |
| CI pipeline details | [`.github/workflows/ci.yml`](.github/workflows/ci.yml) |

Cursor-specific, glob-scoped conventions live in `.cursor/rules/`; this file
stays tool-agnostic on purpose so any agent reads the same source of truth.

## Before opening a PR

- [ ] `pre-commit run --all-files` passes
- [ ] Commit message(s) and PR title are Conventional Commits
- [ ] New/changed endpoints reflected in `docs/api_contracts.md` or
      `docs/endpoints/` if applicable
- [ ] A non-obvious decision (chose X over Y, accepted a known trade-off) gets
      an ADR in `docs/adr/`, not just a commit message
