DOCKER := $(shell \
	if command -v docker-compose >/dev/null 2>&1; then \
		echo docker-compose; \
	elif docker compose version >/dev/null 2>&1; then \
		echo "docker compose"; \
	else \
		echo "ERROR: docker compose not found" >&2; exit 1; \
	fi \
)

run:
	$(DOCKER) -f infra/database.yml up -d db
	uv run -- flask --app app run --debug

# Populate the database
initdb:
	$(DOCKER) -f infra/database.yml up -d db
	sleep 2
	uv run -- flask --app app init-db

deletedb:
	$(DOCKER) -f infra/database.yml down --volumes
	$(DOCKER) -f infra/database.yml rm 

bdcon:
	psql -h localhost -p 5432 -U buska_user -d buska_db
