# Changelog

All notable changes to this project will be documented in this file.

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
