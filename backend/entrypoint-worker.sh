#!/bin/bash
set -e

# Worker waits for the database but does NOT run migrations
# (migrations are handled by the backend container to avoid race conditions).
echo "Waiting for database..."
until python -c "
import os, psycopg2
url = os.environ.get('DATABASE_URL', '').replace('+asyncpg', '+psycopg2')
if not url:
    raise SystemExit(1)
psycopg2.connect(url)
" 2>/dev/null; do
    echo "Database not ready, retrying in 2s..."
    sleep 2
done
echo "Database ready."

echo "Starting worker..."
exec "$@"
