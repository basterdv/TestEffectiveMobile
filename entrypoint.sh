#!/bin/sh
set -e

# Если в скрипт передали кастомную команду
if [ "$#" -gt 0 ]; then
    echo "Running custom command: $*"
    exec "$@"
fi

# Дефолтный сценарий для основного приложения API
echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting application..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
