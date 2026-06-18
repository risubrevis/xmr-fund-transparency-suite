#!/bin/bash
# XMR Fund Transparency Suite — setup and launch script.
#
# Usage:
#   ./scripts/setup.sh           # Prepare data dirs, start production
#   ./scripts/setup.sh --dev     # Prepare data dirs, start development (hot-reload)
#   ./scripts/setup.sh --init    # Only prepare data dirs, do not start containers
#   ./scripts/setup.sh --stop    # Stop containers
#   ./scripts/setup.sh --clean   # Stop containers and remove all data

set -euo pipefail
cd "$(dirname "$0")/.."

# ── Colors ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()  { echo -e "${CYAN}→${NC} $*"; }
ok()    { echo -e "${GREEN}✓${NC} $*"; }
warn()  { echo -e "${YELLOW}!${NC} $*"; }
error() { echo -e "${RED}✗${NC} $*"; }

# ── Defaults ────────────────────────────────────────────────────────────────
DEV=false
INIT_ONLY=false
ACTION=""

# ── Parse arguments ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dev)       DEV=true;  shift ;;
        --init)      INIT_ONLY=true; shift ;;
        --stop)      ACTION=stop; shift ;;
        --clean)     ACTION=clean; shift ;;
        -h|--help)   cat <<HELP
XMR Fund Transparency Suite — setup and launch script.

Usage:
  $(basename "$0") [OPTION]

Options:
  --dev     Start in development mode (hot-reload, logs in foreground)
  --init    Only prepare data directories, do not start containers
  --stop    Stop running containers
  --clean   Stop containers and delete all persistent data
  -h        Show this help

Defaults (no flags):  prepare directories and start in production mode.
HELP
            exit 0 ;;
        *)  error "Unknown option: $1"; exit 1 ;;
    esac
done

# ── Stop ─────────────────────────────────────────────────────────────────────
if [[ "$ACTION" == "stop" ]]; then
    info "Stopping containers..."
    if [[ "$DEV" == true ]]; then
        docker compose -f docker-compose.dev.yml down
    else
        docker compose down
    fi
    ok "Containers stopped."
    exit 0
fi

# ── Clean ────────────────────────────────────────────────────────────────────
if [[ "$ACTION" == "clean" ]]; then
    warn "This will stop all containers and DELETE all persistent data:"
    echo "  postgres/  redis/  monero-wallet-rpc/  data/settings.json"
    echo ""
    read -rp "Continue? [y/N] " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        info "Aborted."
        exit 0
    fi

    info "Stopping containers..."
    docker compose -f docker-compose.dev.yml down -v 2>/dev/null || true
    docker compose down -v 2>/dev/null || true

    info "Removing data directories..."
    sudo rm -rf postgres/ redis/ monero-wallet-rpc/ data/settings.json

    ok "All data removed. Run '$(basename "$0") [--dev]' for a fresh start."
    exit 0
fi

# ── Check .env ───────────────────────────────────────────────────────────────
if [[ ! -f .env ]]; then
    error ".env file not found!"
    info "Copy .env.example to .env and fill in your values:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

# ── Prepare data directories ─────────────────────────────────────────────────
info "Creating data directories..."

mkdir -p postgres redis monero-wallet-rpc data

# monero-wallet-rpc runs as uid=1000(monero) inside the container.
# The bind-mounted host directory must be writable by that user.
sudo chown -R 1000:1000 monero-wallet-rpc

# postgres entrypoint (docker-entrypoint.sh) runs as root and chowns
# the data directory to the postgres user (uid=70) automatically.

# redis with --appendonly yes creates its data files under /data
# and chowns them to the redis user (uid=999) automatically.

# backend writes settings.json and other runtime data to /app/data
# which maps to ./data on the host — owned by the host user.

ok "Data directories ready."

# ── Init-only mode ───────────────────────────────────────────────────────────
if [[ "$INIT_ONLY" == true ]]; then
    echo ""
    info "Directories prepared. Start manually with:"
    echo "  docker compose -f docker-compose.dev.yml up --build   # dev"
    echo "  docker compose up -d --build                          # prod"
    exit 0
fi

# ── Start containers ────────────────────────────────────────────────────────
echo ""
if [[ "$DEV" == true ]]; then
    info "Starting in DEVELOPMENT mode (hot-reload, logs in foreground)..."
    echo ""
    docker compose -f docker-compose.dev.yml up --build
else
    info "Starting in PRODUCTION mode (detached)..."
    echo ""
    docker compose up -d --build
    echo ""
    ok "Containers started."
    info "Dashboard:    http://localhost:3000"
    info "Backend API:  http://localhost:8000/docs"
    info "Monero RPC:   http://localhost:18082"
    echo ""
    info "View logs:    docker compose logs -f"
    info "Stop:          docker compose down  or  $(basename "$0") --stop"
fi
