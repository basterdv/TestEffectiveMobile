FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml ./

RUN uv pip install --system --no-cache -r pyproject.toml

COPY src ./src

COPY alembic.ini ./
COPY alembic ./alembic
COPY entrypoint.sh ./

ENTRYPOINT ["./entrypoint.sh"]

#EXPOSE 8000
#
#CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
#


