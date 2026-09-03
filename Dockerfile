# syntax=docker/dockerfile:1

FROM python:3.13-slim-bookworm AS tests

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PYTHONPATH=/app/src

WORKDIR /app

COPY pyproject.toml poetry.lock README.md ./
RUN python -m pip install "poetry==2.3.1" \
    && poetry install --with test --no-root \
    && poetry run playwright install --with-deps chrome firefox \
    && rm -rf /var/lib/apt/lists/*

COPY src ./src
COPY tests ./tests

CMD ["poetry", "run", "pytest"]
