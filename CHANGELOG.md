# Changelog

All notable changes to this project will be documented in this file.

## [v1.2.0] - 2026-04-11

### Added
- **Incident reporting (`ocorrencia`)** — new `Ocorrencia` model and `POST /ocorrencias` endpoint; alunos and motoristas can report problems (delay, overcrowding, behaviour, cancellation) optionally linked to a trip; gestors list and resolve incidents via `GET /ocorrencias` and `PATCH /ocorrencias/<id>/resolver`
- **Guardian consent flow** — minor students now require parental consent before their registration reaches the gestor; `POST /alunos/signup` triggers a consent e-mail with a signed token; public `GET/POST /alunos/guardian-consent/<token>` endpoints let the guardian approve or refuse without logging in; gestor approves with `POST /alunos/<id>/aprovar`
- **`PENDING_APPROVAL` user status** — new enum value added to `user_status`; aluno registrations from minors land in this state until the gestor approves
- **Dashboard APIs** — `GET /dashboard/viagens/<id>/progresso` (stop-by-stop trip progress for gestors), `GET /dashboard/relatorios/periodo` (operational report for a date range), and `GET /dashboard/viagens/<id>/trajeto-real` (full GPS breadcrumb trail)
- **Routing service** — `GET /routing/route` proxies an OSRM-compatible routing backend and returns turn-by-turn geometry for use in the map components
- **Public institution catalog** — `GET /instituicoes/public` allows unauthenticated lookup of institutions, enabling address auto-complete during student signup
- **IBGE municipality code on `Prefeitura`** — new `codigo_ibge` field (unique, backfilled on migration) to support catalog imports and regional reporting
- **External institution catalog import** — `Instituicao` model extended with `fonte`, `codigo_externo`, `sigla`, `uf`, `prefeitura_id`, `situacao`, `categoria_administrativa`, and `organizacao_academica` for importing from MEC/INEP datasets

### Changed
- `Aluno` model: `nome_pai`/`cpf_pai` renamed to `nome_responsavel`/`cpf_responsavel`; separate `nome_mae`/`cpf_mae` columns dropped; new fields `data_nascimento`, `email_responsavel`, `guardian_token`, and `guardian_consented_at` added to support the consent flow
- `Gestor` model: unused `matricula` and `salario` columns removed
- `alunos/` list endpoint now accepts a `status` query parameter so gestors can filter by `PENDING_APPROVAL`, `ACTIVE`, etc.

### Fixed
- Dropped stale index `idx_password_reset_token_expires_at` that was no longer needed after the password-reset refactor in v1.1.0

---

## [v1.1.0] - 2026-03-10

### Added
- Password reset flow with email sending via SMTP (#19)
- MailHog support for local email development
- Push notification system for users (#16)
- Gestor can provision and manage aluno accounts (#15)
- Endpoint to list motoristas by municipality (#18)
- Backend integration test suite with pytest (#13)
- Test factories and helpers (`PrefeituraFactory`, `UserFactory`, auth helpers)
- Centralized input validation utilities (`app/utils/validators.py`)
- Structured request logging with unique request IDs and security headers
- Error handlers with consistent JSON error contract (`app/core/error_handlers.py`)
- Idempotent `scripts/init-db.sh` for production database initialization
- Ansible automation playbooks for deployment
- Docker production setup (`docker-compose.prod.yml`, `Dockerfile` improvements)
- `user_status` and `signup_completed_at` fields on the user model

### Changed
- CI/CD pipeline overhauled: now runs tests, linting (ruff, black), type checking (mypy), and security audit on every PR (#14)
- Docker setup improved: added `curl` for healthchecks, configurable database port, and a proper `init-db` target in Makefile
- Deployment pipeline now uses a single idempotent `docker-init-db` target
- `make docs-serve` renamed to `make docs`
- Logger refactored to support development (human-readable) and production (JSON) formats

### Fixed
- Authentication validation edge cases
- Motorista and aluno can view route stop points
- Lint and type annotation issues across multiple modules
- Duplicate Makefile rule removed
- Wrong API docs port (`:5001/apidocs` → `:5000/docs`)

---

## [v1.0.0] - 2026-01-27

Initial release.

### Added
- Core multi-tenant architecture scoped by `prefeitura`
- User authentication with JWT (login, registration)
- Role-based access control: `USER`, `ALUNO`, `MOTORISTA`, `GESTOR`
- Routes (`rota`), stops (`ponto`), schedules (`horario_rota`), and trips (`viagem`) management
- Student (`aluno`), driver (`motorista`), and manager (`gestor`) profile management
- School/institution (`instituicao`) and bus (`onibus`) management
- PostGIS spatial support for stop geolocation
- Alembic database migrations
- Flasgger/Swagger API documentation at `/docs`
- Makefile with targets for dev, database, migrations, testing, and Docker
