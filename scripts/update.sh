#!/bin/bash
# XMR Fund Transparency Suite — update script.
#
# Pulls the latest (or specified) release tag and redeploys.
# Database migrations run automatically via the backend entrypoint.
#
# Usage:
#   ./scripts/update.sh              # Update to latest release tag
#   ./scripts/update.sh v0.2.0       # Update to a specific version
#   ./scripts/update.sh --check       # Check for available updates without applying
#   ./scripts/update.sh --rollback    # Roll back to the previous version
#   ./scripts/update.sh --list        # List available release versions
#   ./scripts/update.sh -h            # Show help

set -euo pipefail
cd "$(dirname "$0")/.."

# ── Colors ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()  { echo -e "${CYAN}→${NC} $*"; }
ok()    { echo -e "${GREEN}✓${NC} $*"; }
warn()  { echo -e "${YELLOW}!${NC} $*"; }
error() { echo -e "${RED}✗${NC} $*"; }
header(){ echo -e "\n${BOLD}${CYAN}━━━ $* ━━━${NC}\n"; }

# ── Version file for rollback ────────────────────────────────────────────────
VERSION_FILE=".deploy-version"

save_current_version() {
    # Record what we're currently on so --rollback can return to it.
    local current
    current=$(git describe --tags --exact-match 2>/dev/null || git rev-parse --short HEAD)
    echo "$current" > "$VERSION_FILE"
}

load_previous_version() {
    if [[ -f "$VERSION_FILE" ]]; then
        head -1 "$VERSION_FILE"
    else
        echo ""
    fi
}

# ── Prerequisites ────────────────────────────────────────────────────────────
check_prerequisites() {
    local missing=0

    if ! command -v git >/dev/null 2>&1; then
        error "git is required but not installed."
        missing=1
    fi

    if ! command -v docker >/dev/null 2>&1; then
        error "docker is required but not installed."
        missing=1
    fi

    # docker compose can be a plugin (docker compose) or standalone (docker-compose)
    if docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
    elif command -v docker-compose >/dev/null 2>&1; then
        COMPOSE_CMD="docker-compose"
    else
        error "docker compose (or docker-compose) is required but not installed."
        missing=1
    fi

    if [[ "$missing" -eq 1 ]]; then
        exit 1
    fi
}

# ── Check .env ───────────────────────────────────────────────────────────────
check_env() {
    if [[ ! -f .env ]]; then
        error ".env file not found!"
        echo ""
        info "This usually means the app has not been set up yet."
        info "Run ./scripts/setup.sh first."
        exit 1
    fi
}

# ── Database backup ──────────────────────────────────────────────────────────
backup_database() {
    local backup_dir="backups"
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${backup_dir}/xmrdashboard_${timestamp}.sql"

    mkdir -p "$backup_dir"

    # Only attempt backup if postgres container is running.
    if ! $COMPOSE_CMD ps postgres --format '{{.Status}}' 2>/dev/null | grep -qi 'up\|running'; then
        warn "Postgres container is not running — skipping database backup."
        return 0
    fi

    info "Creating database backup..."
    if $COMPOSE_CMD exec -T postgres pg_dump -U xmruser xmrdashboard > "$backup_file" 2>/dev/null; then
        # Compress the backup
        gzip "$backup_file"
        ok "Database backup saved: ${backup_file}.gz"
    else
        warn "Database backup failed. Continuing anyway — make sure your data is safe."
        rm -f "$backup_file"
    fi
}

# ── Determine current version ────────────────────────────────────────────────
get_current_version() {
    git describe --tags --exact-match 2>/dev/null || echo "$(git rev-parse --short HEAD) (no tag)"
}

# ── Find latest release tag ─────────────────────────────────────────────────
find_latest_tag() {
    # Sort tags by semantic version (vMajor.Minor.Patch)
    git tag -l 'v*' | sort -V | tail -1
}

# ── Check for updates ────────────────────────────────────────────────────────
check_for_updates() {
    info "Fetching tags from remote..."
    git fetch --tags 2>/dev/null

    local latest_tag
    latest_tag=$(find_latest_tag)

    if [[ -z "$latest_tag" ]]; then
        error "No release tags found in the repository."
        exit 1
    fi

    local current
    current=$(git describe --tags --exact-match 2>/dev/null || echo "")

    echo ""
    if [[ -n "$current" && "$current" == "$latest_tag" ]]; then
        ok "Already on the latest version: $latest_tag"
    else
        info "Current version:  ${current:-untagged}"
        info "Latest available: $latest_tag"
        echo ""
        echo -e "  Run ${BOLD}./scripts/update.sh${NC} to update."
    fi
    echo ""
}

# ── List available versions ──────────────────────────────────────────────────
list_versions() {
    info "Fetching tags from remote..."
    git fetch --tags 2>/dev/null

    local current
    current=$(git describe --tags --exact-match 2>/dev/null || echo "")

    echo ""
    echo -e "Available release versions:"
    echo ""
    git tag -l 'v*' | sort -V | while read -r tag; do
        if [[ "$tag" == "$current" ]]; then
            echo -e "  ${GREEN}${tag} (current)${NC}"
        else
            echo "  $tag"
        fi
    done
    echo ""
}

# ── Rollback ─────────────────────────────────────────────────────────────────
do_rollback() {
    local prev_version
    prev_version=$(load_previous_version)

    if [[ -z "$prev_version" ]]; then
        error "No previous version recorded. Cannot rollback."
        info "The .deploy-version file is missing. Rollback is only available after an update."
        exit 1
    fi

    header "Rolling Back"

    info "Rolling back to: $prev_version"

    backup_database

    info "Checking out $prev_version..."
    git checkout "$prev_version"

    info "Rebuilding and restarting containers..."
    $COMPOSE_CMD up -d --build

    # Prune old images
    docker image prune -f >/dev/null 2>&1 || true

    echo "$prev_version" > "$VERSION_FILE"
    ok "Rollback to $prev_version complete!"
    echo ""
    info "View logs: $COMPOSE_CMD logs -f"
}

# ── Main update ──────────────────────────────────────────────────────────────
do_update() {
    local target_version="$1"
    local current_version

    current_version=$(get_current_version)

    header "Updating XMR Fund Transparency Suite"
    info "Current version: $current_version"

    # Save current version for rollback before switching
    save_current_version

    # Fetch tags
    info "Fetching tags from remote..."
    git fetch --tags 2>/dev/null

    # Determine target version
    if [[ -z "$target_version" ]]; then
        target_version=$(find_latest_tag)
        if [[ -z "$target_version" ]]; then
            error "No release tags found in the repository."
            exit 1
        fi
        info "Latest release: $target_version"
    fi

    # Verify the tag exists
    if ! git rev-parse "$target_version" >/dev/null 2>&1; then
        error "Version $target_version not found."
        info "Run './scripts/update.sh --list' to see available versions."
        exit 1
    fi

    # Check if already on this version
    local current_tag
    current_tag=$(git describe --tags --exact-match 2>/dev/null || echo "")
    if [[ "$current_tag" == "$target_version" ]]; then
        ok "Already on version $target_version."
        echo ""
        info "To force a rebuild, run: $COMPOSE_CMD up -d --build"
        exit 0
    fi

    echo ""
    info "Updating to: $target_version"

    # Backup database before switching
    backup_database

    # Stash any local changes that are tracked
    if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
        warn "Uncommitted changes detected — stashing..."
        git stash push -m "pre-update-$(date +%Y%m%d_%H%M%S)" >/dev/null
    fi

    # Checkout the target version
    info "Checking out $target_version..."
    git checkout "$target_version"

    # Rebuild and restart containers
    info "Rebuilding containers..."
    $COMPOSE_CMD up -d --build

    # Wait for backend to be healthy and run migrations
    info "Waiting for backend to start (migrations run automatically)..."
    local retries=30
    local started=false
    while [[ $retries -gt 0 ]]; do
        if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
            started=true
            break
        fi
        retries=$((retries - 1))
        sleep 2
    done

    if [[ "$started" == true ]]; then
        ok "Backend is healthy."
    else
        warn "Backend health check timed out."
        info "Check logs: $COMPOSE_CMD logs backend"
    fi

    # Prune old Docker images
    info "Cleaning up old Docker images..."
    docker image prune -f >/dev/null 2>&1 || true

    # Record deployed version
    echo "$target_version" > "$VERSION_FILE"

    # Clean up old backups (keep last 5)
    local backup_count
    backup_count=$(find backups/ -name '*.sql.gz' 2>/dev/null | wc -l)
    if [[ "$backup_count" -gt 5 ]]; then
        info "Cleaning up old backups (keeping last 5)..."
        ls -1t backups/*.sql.gz 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null || true
    fi

    echo ""
    ok "Update complete! Running version: $target_version"
    echo ""
    info "Dashboard:   http${APP_URL:+s}://${APP_URL:-localhost}"
    info "Backend API: http${APP_URL:+s}://${APP_URL:-localhost}:8000/docs"
    info "View logs:   $COMPOSE_CMD logs -f"
    info "Rollback:     ./scripts/update.sh --rollback"
    echo ""
    warn "If something went wrong, check logs with: $COMPOSE_CMD logs -f"
    warn "To rollback:  ./scripts/update.sh --rollback"
}

# ── Parse arguments ──────────────────────────────────────────────────────────
TARGET_VERSION=""
ACTION=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --check)   ACTION=check; shift ;;
        --rollback) ACTION=rollback; shift ;;
        --list)    ACTION=list; shift ;;
        -h|--help)
            cat <<HELP
XMR Fund Transparency Suite — update script.

Usage:
  $(basename "$0")              # Update to latest release
  $(basename "$0") v0.2.0       # Update to a specific version
  $(basename "$0") --check      # Check for available updates
  $(basename "$0") --rollback    # Roll back to previous version
  $(basename "$0") --list        # List available release versions
  $(basename "$0") -h            # Show this help

The script will:
  1. Create a database backup
  2. Fetch the latest release tags
  3. Checkout the target version
  4. Rebuild and restart Docker containers
  5. Wait for the backend health check

Database migrations run automatically on backend startup.
HELP
            exit 0 ;;
        v*)  TARGET_VERSION="$1"; shift ;;
        *)  error "Unknown option: $1"; exit 1 ;;
    esac
done

# ── Run ───────────────────────────────────────────────────────────────────────
check_prerequisites

case "${ACTION:-update}" in
    check)
        check_env
        check_for_updates
        ;;
    list)
        list_versions
        ;;
    rollback)
        check_env
        do_rollback
        ;;
    update)
        check_env
        do_update "$TARGET_VERSION"
        ;;
esac
