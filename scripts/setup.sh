#!/bin/bash
# XMR Fund Transparency Suite — setup and launch script.
#
# Usage:
#   ./scripts/setup.sh                          # Production (default instance)
#   ./scripts/setup.sh --dev                    # Development (hot-reload)
#   ./scripts/setup.sh --instance=demo          # Demo instance (shifted ports)
#   ./scripts/setup.sh --instance=staging       # Staging instance (shifted ports)
#   ./scripts/setup.sh --instance=NAME --dev    # Custom instance in dev mode
#   ./scripts/setup.sh --init                   # Only prepare data dirs
#   ./scripts/setup.sh --stop                   # Stop containers
#   ./scripts/setup.sh --clean                  # Stop containers and remove all data
#
# Multi-instance: each --instance=NAME gets a unique COMPOSE_PROJECT_NAME and
# a preset of host ports so multiple deployments can coexist on one host
# without port or container-name collisions. See .env.example for details.

set -euo pipefail
cd "$(dirname "$0")/.."

# ── Colors ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

info()  { echo -e "${CYAN}→${NC} $*"; }
ok()    { echo -e "${GREEN}✓${NC} $*"; }
warn()  { echo -e "${YELLOW}!${NC} $*"; }
error() { echo -e "${RED}✗${NC} $*"; }

# ── Defaults ────────────────────────────────────────────────────────────────
DEV=false
INIT_ONLY=false
ACTION=""
INSTANCE="prod"

# ── Instance presets ─────────────────────────────────────────────────────────
# Each instance gets: COMPOSE_PROJECT_NAME, host ports, APP_URL, ENVIRONMENT.
# Format: "PROJECT_NAME FRONTEND_PORT BACKEND_PORT POSTGRES_PORT REDIS_PORT MONERO_RPC_PORT APP_URL ENVIRONMENT"
get_instance_config() {
    case "$1" in
        prod)
            echo "xmrfts-prod 3000 8000 5432 6379 18082 dashboard.xmrfts.com production"
            ;;
        demo)
            echo "xmrfts-demo 3001 8001 5433 6380 18083 demo.xmrfts.com production"
            ;;
        staging)
            echo "xmrfts-staging 3002 8002 5434 6381 18084 staging.xmrfts.com staging"
            ;;
        *)
            # Unknown instance: use prod port defaults and warn.
            # The user must manually adjust ports in .env to avoid collisions.
            echo "xmrfts-$1 3000 8000 5432 6379 18082 localhost production"
            ;;
    esac
}

# ── Parse arguments ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dev)       DEV=true;  shift ;;
        --init)      INIT_ONLY=true; shift ;;
        --instance=*) INSTANCE="${1#*=}"; shift ;;
        --stop)      ACTION=stop; shift ;;
        --clean)     ACTION=clean; shift ;;
        -h|--help)   cat <<HELP
XMR Fund Transparency Suite — setup and launch script.

Usage:
  $(basename "$0") [OPTION]

Options:
  --dev               Start in development mode (hot-reload, debug logs)
  --instance=NAME     Deploy as instance NAME (default: prod)
                      Presets: prod, demo, staging
                      Each instance gets a unique COMPOSE_PROJECT_NAME and
                      a preset of host ports for isolation on a shared host.
  --init              Only prepare data directories, do not start containers
  --stop              Stop running containers
  --clean             Stop containers and delete all persistent data
  -h                  Show this help

Defaults (no flags):  prepare directories and start in production mode.

Multi-instance examples:
  $(basename "$0")                              # Production (prod)
  $(basename "$0") --instance=demo              # Public demo
  $(basename "$0") --instance=staging --dev     # Staging in dev mode

Instance port presets (frontend / backend / postgres / redis / monero-rpc):
  prod:     3000 / 8000 / 5432 / 6379 / 18082
  demo:     3001 / 8001 / 5433 / 6380 / 18083
  staging:  3002 / 8002 / 5434 / 6381 / 18084
HELP
            exit 0 ;;
        *)  error "Unknown option: $1"; exit 1 ;;
    esac
done

# ── Resolve instance config ──────────────────────────────────────────────────
IFS=' ' read -r COMPOSE_PROJECT_NAME FRONTEND_PORT BACKEND_PORT POSTGRES_PORT REDIS_PORT MONERO_RPC_PORT INSTANCE_APP_URL INSTANCE_ENVIRONMENT \
    <<< "$(get_instance_config "$INSTANCE")"

# ── Stop ─────────────────────────────────────────────────────────────────────
if [[ "$ACTION" == "stop" ]]; then
    info "Stopping containers (instance: $INSTANCE)..."
    export COMPOSE_PROJECT_NAME
    docker compose down
    ok "Containers stopped."
    exit 0
fi

# ── Clean ────────────────────────────────────────────────────────────────────
if [[ "$ACTION" == "clean" ]]; then
    warn "This will stop all containers and DELETE all persistent data for instance '$INSTANCE':"
    echo "  postgres/  redis/  monero-wallet-rpc/  data/settings.json"
    echo ""
    read -rp "Continue? [y/N] " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        info "Aborted."
        exit 0
    fi

    info "Stopping containers (instance: $INSTANCE)..."
    export COMPOSE_PROJECT_NAME
    docker compose down -v 2>/dev/null || true

    info "Removing data directories..."
    sudo rm -rf postgres/ redis/ monero-wallet-rpc/ data/settings.json

    ok "All data removed. Run '$(basename "$0") [--instance=NAME] [--dev]' for a fresh start."
    exit 0
fi

# ── .env setup ──────────────────────────────────────────────────────────────
GENERATED_API_KEY=""

if [[ ! -f .env ]]; then
    if [[ ! -f .env.example ]]; then
        error ".env.example not found! Cannot generate .env file."
        exit 1
    fi

    info "Creating .env from .env.example with auto-generated secrets..."
    info "Instance: $INSTANCE  (project: $COMPOSE_PROJECT_NAME)"

    # Warn if using a non-preset instance with default ports
    if [[ "$INSTANCE" != "prod" && "$INSTANCE" != "demo" && "$INSTANCE" != "staging" ]]; then
        warn "Instance '$INSTANCE' has no port preset — using prod defaults."
        warn "Edit .env to set unique host ports before starting alongside other instances."
    fi

    # Generate secure random values using standard Linux tools.
    # openssl is available on virtually all Linux servers.
    DB_PASSWORD=$(openssl rand -hex 16)
    API_KEY=$(openssl rand -hex 32)
    # Fernet requires at least 32 bytes; 64 hex chars = 32 bytes
    VIEW_KEY_MASTER_SECRET=$(openssl rand -hex 32)

    # Copy .env.example and replace secrets
    cp .env.example .env

    # Replace placeholder values with generated secrets
    sed -i "s|^DB_PASSWORD=.*|DB_PASSWORD=${DB_PASSWORD}|" .env
    sed -i "s|^API_KEY=.*|API_KEY=${API_KEY}|" .env
    sed -i "s|^VIEW_KEY_MASTER_SECRET=.*|VIEW_KEY_MASTER_SECRET=${VIEW_KEY_MASTER_SECRET}|" .env

    # Update DATABASE_URL with the generated password
    sed -i "s|^DATABASE_URL=.*|DATABASE_URL=postgresql+asyncpg://xmruser:${DB_PASSWORD}@postgres/xmrdashboard|" .env

    # Set instance-specific configuration (project name, ports, app url, environment)
    sed -i "s|^COMPOSE_PROJECT_NAME=.*|COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME}|" .env
    sed -i "s|^FRONTEND_PORT=.*|FRONTEND_PORT=${FRONTEND_PORT}|" .env
    sed -i "s|^BACKEND_PORT=.*|BACKEND_PORT=${BACKEND_PORT}|" .env
    sed -i "s|^POSTGRES_PORT=.*|POSTGRES_PORT=${POSTGRES_PORT}|" .env
    sed -i "s|^REDIS_PORT=.*|REDIS_PORT=${REDIS_PORT}|" .env
    sed -i "s|^MONERO_RPC_PORT=.*|MONERO_RPC_PORT=${MONERO_RPC_PORT}|" .env
    sed -i "s|^APP_URL=.*|APP_URL=${INSTANCE_APP_URL}|" .env
    sed -i "s|^ENVIRONMENT=.*|ENVIRONMENT=${INSTANCE_ENVIRONMENT}|" .env

    # Save the API key for display at the end
    GENERATED_API_KEY="$API_KEY"

    ok ".env created with auto-generated secrets for instance '$INSTANCE'."
else
    # .env already exists — read instance config from it
    COMPOSE_PROJECT_NAME=$(grep -E "^COMPOSE_PROJECT_NAME=" .env 2>/dev/null | head -1 | cut -d= -f2- || echo "")
    BACKEND_PORT=$(grep -E "^BACKEND_PORT=" .env 2>/dev/null | head -1 | cut -d= -f2- || echo "8000")
    FRONTEND_PORT=$(grep -E "^FRONTEND_PORT=" .env 2>/dev/null | head -1 | cut -d= -f2- || echo "3000")

    if [[ -n "$COMPOSE_PROJECT_NAME" ]]; then
        info "Using existing .env (project: $COMPOSE_PROJECT_NAME)."
    else
        # .env predates multi-instance support — derive project name from directory
        COMPOSE_PROJECT_NAME=$(basename "$(pwd)")
        # Sanitize: docker compose lowercases and replaces invalid chars
        COMPOSE_PROJECT_NAME=$(echo "$COMPOSE_PROJECT_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9_-]//g')
        info "Using existing .env (project from directory: $COMPOSE_PROJECT_NAME)."
    fi

    # Extract API_KEY to display at the end
    GENERATED_API_KEY=$(grep -E "^API_KEY=" .env 2>/dev/null | head -1 | cut -d= -f2- || true)
    if [[ -z "$GENERATED_API_KEY" ]]; then
        GENERATED_API_KEY=""
    fi
fi

# Export so docker compose uses the correct project name even if .env
# variable reading is unreliable in some compose versions.
export COMPOSE_PROJECT_NAME

# ── Prepare data directories ─────────────────────────────────────────────────
echo ""
info "The next step requires sudo to set ownership on data directories"
info "used by Docker containers (monero-wallet-rpc needs uid 1000)."
info "You may be prompted for your sudo password."
echo ""

info "Creating data directories..."

mkdir -p postgres redis monero-wallet-rpc data

# monero-wallet-rpc runs as uid=1000(monero) inside the container.
# The bind-mounted host directory must be writable by that user.
sudo chown -R 1000:1000 monero-wallet-rpc

ok "Data directories ready."

# ── Init-only mode ───────────────────────────────────────────────────────────
if [[ "$INIT_ONLY" == true ]]; then
    echo ""
    info "Directories prepared. Start manually with:"
    echo "  ./scripts/setup.sh                          # production"
    echo "  ./scripts/setup.sh --dev                    # development"
    echo "  ./scripts/setup.sh --instance=demo          # demo instance"
    echo "  ./scripts/setup.sh --instance=staging        # staging instance"
    exit 0
fi

# ── Start containers ────────────────────────────────────────────────────────
echo ""
if [[ "$DEV" == true ]]; then
    info "Starting instance '$INSTANCE' in DEVELOPMENT mode (hot-reload, foreground)..."
    info "Ports: frontend=${FRONTEND_PORT} backend=${BACKEND_PORT}"
    echo ""
    export INSTALL_DEV=true
    export FRONTEND_TARGET=dev
    export FRONTEND_INTERNAL_PORT=3000
    export LOG_LEVEL=DEBUG
    export LOG_FORMAT=text
    export RESTART_POLICY=no
    export BACKEND_COMMAND="uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    export WORKER_COMMAND='watchfiles "python -m worker.scanner" /app/app /app/worker'
    docker compose up --build
else
    info "Starting instance '$INSTANCE' in PRODUCTION mode (detached)..."
    info "Ports: frontend=${FRONTEND_PORT} backend=${BACKEND_PORT}"
    echo ""
    docker compose up -d --build
    echo ""
    ok "Containers started (instance: $INSTANCE, project: $COMPOSE_PROJECT_NAME)."
    APP_URL_DISPLAY=$(grep -E "^APP_URL=" .env 2>/dev/null | head -1 | cut -d= -f2- || echo "localhost")
    info "Dashboard:    https://${APP_URL_DISPLAY}"
    info "Backend API:  https://${APP_URL_DISPLAY}/docs"
    info "Monero RPC:   http://localhost:${MONERO_RPC_PORT:-18082}"
    echo ""
    info "View logs:    docker compose logs -f"
    info "Stop:          docker compose down  or  $(basename "$0") --stop"
fi

# ── Post-setup information ──────────────────────────────────────────────────
echo ""
echo -e "${BOLD}━━━ Setup Complete ━━━${NC}"
echo ""

if [[ -n "$GENERATED_API_KEY" ]]; then
    # Check if the API key is still a placeholder
    if [[ "$GENERATED_API_KEY" == changeme* ]]; then
        warn "⚠  API Key is still set to the default value!"
        echo "   Generate a new one with:  openssl rand -hex 32"
        echo "   Then update it in .env:   API_KEY=<your-new-key>"
        echo ""
    else
        echo -e "${GREEN}Your API Key (save this — you need it to log in):${NC}"
        echo ""
        echo -e "  ${BOLD}${GENERATED_API_KEY}${NC}"
        echo ""
        warn "This key will NOT be shown again. Save it now!"
        echo ""
    fi
fi

echo -e "${YELLOW}⚠  Review these settings in .env before using in production:${NC}"
echo ""
echo "  COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME}"
echo "  ENVIRONMENT=$(grep -E '^ENVIRONMENT=' .env 2>/dev/null | head -1 | cut -d= -f2- || echo 'local')"
echo "  APP_URL=$(grep -E '^APP_URL=' .env 2>/dev/null | head -1 | cut -d= -f2- || echo 'localhost')"
echo "  FRONTEND_PORT=${FRONTEND_PORT}  BACKEND_PORT=${BACKEND_PORT}"
echo ""
echo -e "Edit with:  ${CYAN}nano .env${NC}"
echo ""
