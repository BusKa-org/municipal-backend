run:
	docker-compose -f infra/database.yml up -d db
	uv run -- flask --app app run --debug

# Populate the database
initdb:
	uv run -- flask --app app init-db

deletedb:
	docker-compose -f infra/database.yml down --volumes
	docker-compose -f infra/database.yml rm 

bdcon:
	psql -h localhost -p 5432 -U buska_user -d buska_db
