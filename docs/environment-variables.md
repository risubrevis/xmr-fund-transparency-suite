# Environment Variables

All configuration is injected via the `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_PASSWORD` | *(auto-generated)* | PostgreSQL password |
| `API_KEY` | `changeme` | Admin API key (64 hex chars) |
| `VIEW_KEY_MASTER_SECRET` | `changeme` | Master secret for Fernet AES-256 encryption (≥ 32 bytes) |
| `MONERO_RPC_URL` | `http://monero-wallet-rpc:18082/json_rpc` | `monero-wallet-rpc` endpoint |
| `MONERO_DAEMON_ADDRESS` | `xmr.letmego.me:18089` | Daemon address for wallet sync |
| `SCAN_INTERVAL` | `60` | Seconds between background scans |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `LOG_FORMAT` | `json` | `json` or `console` |
| `ENVIRONMENT` | `local` | `local` / `staging` / `production` |
| `APP_URL` | `localhost` | Used for CORS and widget origin |
| `COMPOSE_PROJECT_NAME` | `xmrfts-prod` | Docker Compose project name — instance isolation (see [Multi-Instance Deployment](./multi-instance.md)) |
| `FRONTEND_PORT` | `3000` | Host port for the frontend container |
| `BACKEND_PORT` | `8000` | Host port for the backend container |
| `POSTGRES_PORT` | `5432` | Host port for PostgreSQL |
| `REDIS_PORT` | `6379` | Host port for Redis |
| `MONERO_RPC_PORT` | `18082` | Host port for `monero-wallet-rpc` |
| `CORS_ORIGINS` | *(empty)* | Additional comma-separated CORS origins |
| `SENTRY_DSN` | *(empty)* | Optional Sentry error tracking DSN |

> **Security note:** Generate `VIEW_KEY_MASTER_SECRET` with `openssl rand -hex 32`. It must be at least 32 bytes.