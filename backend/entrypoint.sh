#!/bin/bash
set -e

# Run database migrations unless SKIP_MIGRATIONS is set.
# Only the backend container should run migrations to avoid race conditions.
if [ "${SKIP_MIGRATIONS:-false}" != "true" ]; then
    echo "Running database migrations..."
    alembic upgrade head
fi

# Wait for database if WAIT_FOR_DB is set (used by worker).
if [ "${WAIT_FOR_DB:-false}" = "true" ]; then
    echo "Waiting for database..."
    until python -c "
import os, psycopg2
url = os.environ.get('DATABASE_URL', '').replace('+asyncpg', '')
if not url:
    raise SystemExit(1)
psycopg2.connect(url)
"; do
        echo "Database not ready, retrying in 2s..."
        sleep 2
    done
    echo "Database ready."
fi

echo "Starting application..."
exec "$@"
