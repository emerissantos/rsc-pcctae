.PHONY: env up down build logs shell migrate makemigrations test check lint collectstatic

env:
	python scripts/init_env.py

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f web

shell:
	docker compose exec web python manage.py shell

migrate:
	docker compose exec web python manage.py migrate

makemigrations:
	docker compose exec web python manage.py makemigrations

test:
	docker compose exec web pytest

check:
	docker compose exec web python manage.py check

lint:
	docker compose exec web ruff check .

collectstatic:
	docker compose exec web python manage.py collectstatic --noinput
