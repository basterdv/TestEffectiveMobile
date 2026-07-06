FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml ./

RUN uv sync --no-dev --no-install-project

COPY src ./src
COPY alembic.ini ./
COPY alembic ./alembic
COPY entrypoint.sh ./

RUN chmod +x entrypoint.sh

RUN uv sync --no-dev

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT ["./entrypoint.sh"]

