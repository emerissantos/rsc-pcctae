FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY config ./config
COPY apps ./apps
RUN pip install --no-cache-dir -e '.[dev]'

COPY . .
RUN chmod +x /app/docker/django/entrypoint.sh

ENTRYPOINT ["/app/docker/django/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
