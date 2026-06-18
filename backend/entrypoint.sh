#!/bin/bash
set -e

# Run database migrations unless SKIP_MIGRATIONS is set.
# Only the backend container should run migrations to avoid race conditions.
if [ "${SKIP_MIGRATIONS:-false}" != "true" ]; then
    echo "Running database migrations..."
    alembic upgrade head
fi

echo "Starting application..."
exec "$@"
