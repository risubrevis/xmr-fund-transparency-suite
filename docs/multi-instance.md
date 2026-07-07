# Multi-Instance Deployment

Multiple isolated instances (production, demo, staging, etc.) can run on the **same host** without port or container-name collisions. Each instance lives in its own directory with its own `.env`, Docker Compose project name, host ports, and data volumes.

## How It Works

The `--instance=NAME` flag tells `setup.sh` to generate a `.env` with a unique `COMPOSE_PROJECT_NAME` and a preset of non-overlapping host ports:

| Instance | Project name | Frontend | Backend | Postgres | Redis | Monero RPC | APP_URL | Environment |
|----------|-------------|----------|---------|----------|-------|------------|---------|-------------|
| `prod` (default) | `xmrfts-prod` | 3000 | 8000 | 5432 | 6379 | 18082 | `dashboard.xmrfts.com` | production |
| `demo` | `xmrfts-demo` | 3001 | 8001 | 5433 | 6380 | 18083 | `demo.xmrfts.com` | production |
| `staging` | `xmrfts-staging` | 3002 | 8002 | 5434 | 6381 | 18084 | `staging.xmrfts.com` | staging |
| custom | `xmrfts-{name}` | 3000 | 8000 | 5432 | 6379 | 18082 | `localhost` | production |

For custom instance names, prod port defaults are used and the script prints a warning — edit `.env` to set unique host ports before starting alongside other instances.

## Isolation Guarantees

| Resource | Mechanism |
|----------|----------|
| **Container names** | `COMPOSE_PROJECT_NAME` prefix — each instance gets unique names (`xmrfts-prod-backend-1` vs `xmrfts-demo-backend-1`) |
| **Docker networks** | Compose creates a separate bridge network per project — no cross-talk by service name |
| **Host ports** | `FRONTEND_PORT`, `BACKEND_PORT`, `POSTGRES_PORT`, `REDIS_PORT`, `MONERO_RPC_PORT` — each instance uses a unique set |
| **Data volumes** | Bind-mounts (`./postgres`, `./redis`, `./monero-wallet-rpc`, `./data`) are relative to each instance directory |
| **Secrets** | Each instance has its own `.env` with independently generated `DB_PASSWORD`, `API_KEY`, `VIEW_KEY_MASTER_SECRET` |
| **Database** | Each instance runs its own PostgreSQL container with a separate data directory |
| **Git state** | Each instance is a separate clone — `update.sh` updates or rolls back each independently |

## Example: Production + Demo on One Server

```bash
# ── Production (ports 3000 / 8000) ──────────────────────────────────────────
git clone https://github.com/risubrevis/xmr-fund-transparency-suite.git \
    /home/user/dashboard.xmrfts.com
cd /home/user/dashboard.xmrfts.com
./scripts/setup.sh
#   → .env: COMPOSE_PROJECT_NAME=xmrfts-prod, ports 3000/8000/5432/6379/18082

# ── Demo (ports 3001 / 8001) ────────────────────────────────────────────────
git clone https://github.com/risubrevis/xmr-fund-transparency-suite.git \
    /home/user/demo.xmrfts.com
cd /home/user/demo.xmrfts.com
./scripts/setup.sh --instance=demo
#   → .env: COMPOSE_PROJECT_NAME=xmrfts-demo, ports 3001/8001/5433/6380/18083
```

Each instance must be in its own directory with its own git clone.

## Updating a Specific Instance

`update.sh` reads `COMPOSE_PROJECT_NAME` and `BACKEND_PORT` from `.env`, so it automatically targets the correct instance:

```bash
cd /home/user/demo.xmrfts.com
./scripts/update.sh --instance=demo
```

## Nginx for Multiple Instances

Each instance needs its own nginx `server` block pointing to its host ports. Production-grade configs with TLS 1.3, security headers, SSE support, and separate rate-limit zones are provided in the [docs repository](https://github.com/risubrevis/xmr-fund-transparency-suite-docs):

| Domain | Frontend | Backend | Config file |
|--------|----------|--------|-------------|
| `dashboard.xmrfts.com` | `127.0.0.1:3000` | `127.0.0.1:8000` | `dashboard.xmrfts.com.nginx.conf` |
| `demo.xmrfts.com` | `127.0.0.1:3001` | `127.0.0.1:8001` | `demo.xmrfts.com.nginx.conf` |
| `staging.xmrfts.com` | `127.0.0.1:3002` | `127.0.0.1:8002` | *(create by analogy)* |

Demo uses separate rate-limit zones (`api_limit_demo`, `sse_limit_demo`, `export_limit_demo`) so its traffic cannot exhaust the production rate-limit buckets. These zones must be added to `/etc/nginx/conf.d/rate_limiting.conf` (see `rate_limiting.nginx..conf` in the docs repo).

## ⚠️ Migration Note for Existing Deployments

If you have an existing deployment that was started **before** multi-instance support, its `.env` does not contain `COMPOSE_PROJECT_NAME`. In that case Docker Compose derives the project name from the directory name. **Do not add `COMPOSE_PROJECT_NAME` to an existing `.env` with a different value** — this would orphan the existing containers and volumes (they'd be left under the old project name). Either:

- Leave `COMPOSE_PROJECT_NAME` unset (keep using the directory-derived name), or
- Set it to the current directory-derived name (lowercase, alphanumeric only).

New deployments (fresh `setup.sh` run) always set `COMPOSE_PROJECT_NAME` explicitly.