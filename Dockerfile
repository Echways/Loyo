FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VENV=false \
    POETRY_NO_INTERACTION=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential gcc libpq-dev curl ca-certificates netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md /app/

RUN pip install --no-cache-dir "poetry>=1.5.0" \
    && poetry config virtualenvs.create false \
    && poetry install --only main --no-root --no-interaction --no-ansi

RUN pip install --no-cache-dir pydantic-settings || true

COPY . /app

COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

RUN useradd --create-home --shell /bin/bash botuser \
    && chown -R botuser:botuser /app

USER botuser
WORKDIR /app

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "app_run.py"]
