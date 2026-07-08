#!/bin/bash
# XMR Fund Transparency Suite — update script (archive/release-based).
#
# Downloads the latest (or specified) release archive from GitHub Releases and
# redeploys. Works from a plain extracted archive install — no git clone or git
# binary required. Database migrations run automatically via the backend
# entrypoint.
#
# The update replaces the application code in place while preserving all
# persistent state (.env, data dirs, deploy-version markers) by moving it into the
# newly extracted tree and swapping directories.
#
# Usage:
#   ./scripts/update.sh              # Update to latest release
#   ./scripts/update.sh v0.2.0       # Update to a specific version
#   ./scripts/update.sh --check      # Check for available updates without applying
#   ./scripts/update.sh --rollback   # Roll back to the previous version
#   ./scripts/update.sh --list       # List available release versions
#   ./scripts/update.sh --instance=NAME  # Operate on a specific instance (reads .env)
#   ./scripts/update.sh -h          # Show help

set -euo pipefail
cd "$(dirname "$0")/.."

# Absolute path of the application directory — used for the directory swap.
APP_DIR=$(pwd)
PARENT="${APP_DIR%/*}"

# ── Config ──────────────────────────────────────────────────────────────────
GITHUB_REPO="risubrevis/xmr-fund-transparency-suite"
API_BASE="https://api.github.com/repos/${GITHUB_REPO}"
RELEASE_BASE="https://github.com/${GITHUB_REPO}/releases/download"

# Files/dirs preserved across the code swap. Everything else is replaced with
# the freshly downloaded release tree.
PRESERVE=(.env .deploy-version .deploy-previous data postgres redis monero-wallet-rpc backups .git)

VERSION_FILE=".deploy-version"
PREV_FILE=".deploy-previous"

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

# ── Prerequisites ────────────────────────────────────────────────────────────
check_prerequisites() {
    local missing=0

    for cmd in docker curl tar; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            error "$cmd is required but not installed."
            missing=1
        fi
    done

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

# ── Load instance config from .env ───────────────────────────────────────────
# Reads COMPOSE_PROJECT_NAME and BACKEND_PORT from .env so the update targets the
# correct Docker Compose project and health-checks the right port.
load_env_config() {
    COMPOSE_PROJECT_NAME=$(grep -E "^COMPOSE_PROJECT_NAME=" .env 2>/dev/null | head -1 | cut -d= -f2- || echo "")
    BACKEND_PORT=$(grep -E "^BACKEND_PORT=" .env 2>/dev/null | head -1 | cut -d= -f2- || echo "8000")
    APP_URL=$(grep -E "^APP_URL=" .env 2>/dev/null | head -1 | cut -d= -f2- || echo "localhost")

    if [[ -z "$COMPOSE_PROJECT_NAME" ]]; then
        # .env predates multi-instance support — derive project name from directory
        COMPOSE_PROJECT_NAME=$(basename "$(pwd)")
        COMPOSE_PROJECT_NAME=$(echo "$COMPOSE_PROJECT_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9_-]//g')
    fi

    export COMPOSE_PROJECT_NAME

    if [[ -n "$INSTANCE" ]]; then
        info "Instance: $INSTANCE  (project: $COMPOSE_PROJECT_NAME, backend port: $BACKEND_PORT)"
    fi
}

# ── GitHub API helpers ──────────────────────────────────────────────────────
# Optional GITHUB_TOKEN env var raises the unauthenticated 60 req/hr rate limit.
github_api_get() {
    local url="$1"
    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
        curl -fsSL -H "Authorization: Bearer ${GITHUB_TOKEN}" \
                  -H "Accept: application/vnd.github+json" "$url"
    else
        curl -fsSL -H "Accept: application/vnd.github+json" "$url"
    fi
}

get_latest_tag() {
    github_api_get "${API_BASE}/releases/latest" \
        | grep -oE '"tag_name"[[:space:]]*:[[:space:]]*"[^"]+"' \
        | head -1 | sed -E 's/.*"([^"]+)"$/\1/'
}

list_releases() {
    github_api_get "${API_BASE}/releases?per_page=50" \
        | grep -oE '"tag_name"[[:space:]]*:[[:space:]]*"[^"]+"' \
        | sed -E 's/.*"([^"]+)"$/\1/'
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
        gzip "$backup_file"
        ok "Database backup saved: ${backup_file}.gz"
    else
        warn "Database backup failed. Continuing anyway — make sure your data is safe."
        rm -f "$backup_file"
    fi
}

# ── Version state ────────────────────────────────────────────────────────────
# Current/previous versions are tracked in files (no git dependency). When the
# marker is absent (e.g. first update of an archive install), infer the current
# version from the backend source so rollback has something to return to.
get_current_version() {
    if [[ -f "$VERSION_FILE" ]]; then
        local v
        v=$(head -1 "$VERSION_FILE" 2>/dev/null || true)
        if [[ -n "$v" ]]; then echo "$v"; return; fi
    fi
    if [[ -f backend/app/main.py ]]; then
        local v
        v=$(grep -oE 'version[[:space:]]*=[[:space:]]*"[0-9][0-9.]*"' backend/app/main.py \
            | head -1 | sed -E 's/.*"([^"]+)"/\1/')
        if [[ -n "$v" ]]; then echo "v${v}"; return; fi
    fi
    echo "unknown"
}

get_previous_version() {
    if [[ -f "$PREV_FILE" ]]; then
        head -1 "$PREV_FILE" 2>/dev/null || echo ""
    else
        echo ""
    fi
}

normalize_version() {
    local v="$1"
    [[ "$v" != v* ]] && v="v${v}"
    echo "$v"
}

# ── Download a release archive ──────────────────────────────────────────────
# Tries, in order: the discovered release asset, a constructed asset URL, and
# GitHub's auto-generated tarball. Validates the result is a non-empty gzip.
download_release() {
    local tag="$1" out="$2"
    local ver="${tag#v}"
    local json discovered

    json=$(github_api_get "${API_BASE}/releases/tags/${tag}" 2>/dev/null || echo "")
    discovered=$(printf '%s\n' "$json" \
        | grep -oE '"browser_download_url"[[:space:]]*:[[:space:]]*"[^"]+"' \
        | sed -E 's/.*"([^"]+)"$/\1/' \
        | grep '\.tar\.gz$' | head -1)

    local urls=(
        "$discovered"
        "${RELEASE_BASE}/${tag}/xmr-fund-transparency-suite-${ver}.tar.gz"
        "${API_BASE}/tarball/${tag}"
    )

    for url in "${urls[@]}"; do
        [[ -z "$url" ]] && continue
        info "Downloading ${url}"
        if curl -fL --retry 3 -o "$out" "$url" \
           && [[ -s "$out" ]] \
           && gzip -t "$out" 2>/dev/null; then
            return 0
        fi
        rm -f "$out"
    done

    error "Could not download a release archive for ${tag}."
    return 1
}

# ── Health check ─────────────────────────────────────────────────────────────
wait_health() {
    info "Waiting for backend to start (migrations run automatically)..."
    local retries=30 started=false port="${BACKEND_PORT:-8000}"
    while [[ $retries -gt 0 ]]; do
        if curl -sf "http://localhost:${port}/health" >/dev/null 2>&1; then
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
}

# ── Deploy a given release tag ──────────────────────────────────────────────
# Shared by update and rollback. Downloads + extracts the archive, stops
# containers, swaps the code directory (preserving state), rebuilds, and waits
# for health.
deploy_version() {
    local tag="$1"

    info "Updating to: ${tag}"

    # Stage the extraction next to the app dir so the directory swap is a series
    # of same-filesystem renames (instant even for large postgres data).
    local staging
    staging=$(mktemp -d -p "$PARENT" xmrfts-update.XXXXXX 2>/dev/null || mktemp -d)
    local archive="$staging/release.tar.gz"

    if ! download_release "$tag" "$archive"; then
        rm -rf "$staging"
        exit 1
    fi

    info "Extracting archive..."
    if ! tar -xzf "$archive" -C "$staging"; then
        rm -rf "$staging"
        error "Failed to extract archive."
        exit 1
    fi

    local repodir
    repodir=$(find "$staging" -mindepth 1 -maxdepth 1 -type d | head -1)
    if [[ -z "$repodir" || ! -d "$repodir" ]]; then
        rm -rf "$staging"
        error "Archive did not contain a top-level directory."
        exit 1
    fi

    # Stop containers before the swap so no running bind-mount references the
    # data directories while they are being moved.
    info "Stopping containers..."
    $COMPOSE_CMD down >/dev/null 2>&1 || warn "compose down reported an error (continuing)."

    local old="${APP_DIR}.old.$(date +%s)"

    # Swap: move current dir aside, put new code in place, then carry preserved
    # state over. On failure at the critical step, restore the original dir.
    if ! mv "$APP_DIR" "$old"; then
        rm -rf "$staging"
        error "Could not move the current application directory aside."
        exit 1
    fi
    if ! mv "$repodir" "$APP_DIR"; then
        mv "$old" "$APP_DIR" || true
        rm -rf "$staging"
        error "Could not place the new release into ${APP_DIR}."
        exit 1
    fi

    local item
    for item in "${PRESERVE[@]}"; do
        if [[ -e "$old/$item" ]]; then
            mv "$old/$item" "$APP_DIR/$item" || warn "Could not preserve ${item} (kept in ${old})."
        fi
    done

    # Re-enter the new application directory for the build step.
    cd "$APP_DIR"
    rm -rf "$staging"

    info "Rebuilding containers..."
    if ! $COMPOSE_CMD up -d --build; then
        error "Container build/start failed."
        warn "Old code retained at: ${old}"
        warn "Inspect logs: $COMPOSE_CMD logs -f"
        exit 1
    fi

    wait_health

    # Prune old Docker images
    info "Cleaning up old Docker images..."
    docker image prune -f >/dev/null 2>&1 || true

    # Remove the superseded tree now that the new version is up. Its persisted
    # state has already been carried into the new tree.
    rm -rf "$old"
}

# ── Check for updates ───────────────────────────────────────────────────────
check_for_updates() {
    info "Checking for updates..."
    local latest
    latest=$(get_latest_tag) || latest=""
    if [[ -z "$latest" ]]; then
        error "Could not fetch the latest release from GitHub."
        info "Check network connectivity, or set GITHUB_TOKEN if rate-limited."
        exit 1
    fi

    local current
    current=$(get_current_version)

    echo ""
    if [[ "$current" == "$latest" ]]; then
        ok "Already on the latest version: $latest"
    else
        info "Current version:  ${current}"
        info "Latest available: $latest"
        echo ""
        echo -e "  Run ${BOLD}./scripts/update.sh${NC} to update."
    fi
    echo ""
}

# ── List available versions ──────────────────────────────────────────────────
list_versions() {
    info "Fetching releases..."
    local current
    current=$(get_current_version)

    echo ""
    echo -e "Available release versions:"
    echo ""
    list_releases | while read -r tag; do
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
    local prev
    prev=$(get_previous_version)
    if [[ -z "$prev" || "$prev" == "unknown" ]]; then
        error "No previous version recorded. Cannot rollback."
        info "Rollback is only available after an update performed by this script."
        exit 1
    fi

    local cur
    cur=$(get_current_version)

    header "Rolling Back"
    info "Rolling back from ${cur} to ${prev}"

    backup_database

    # Record the version we are leaving so a subsequent rollback can roll forward.
    echo "$cur" > "$PREV_FILE"

    deploy_version "$prev"

    echo "$prev" > "$VERSION_FILE"
    ok "Rollback to ${prev} complete!"
    echo ""
    info "View logs: $COMPOSE_CMD logs -f"
}

# ── Main update ──────────────────────────────────────────────────────────────
do_update() {
    local target="$1"
    local current
    current=$(get_current_version)

    header "Updating XMR Fund Transparency Suite"
    info "Current version: ${current}"

    if [[ -z "$target" ]]; then
        target=$(get_latest_tag) || target=""
        if [[ -z "$target" ]]; then
            error "Could not fetch the latest release from GitHub."
            info "Check network connectivity, or set GITHUB_TOKEN if rate-limited."
            exit 1
        fi
        info "Latest release: ${target}"
    else
        target=$(normalize_version "$target")
    fi

    if [[ "$current" == "$target" ]]; then
        ok "Already on version ${target}."
        echo ""
        info "To force a rebuild, run: $COMPOSE_CMD up -d --build"
        exit 0
    fi

    # Record current version so --rollback can return to it.
    echo "$current" > "$PREV_FILE"

    backup_database

    deploy_version "$target"

    echo "$target" > "$VERSION_FILE"

    # Clean up old backups (keep last 5)
    local backup_count
    backup_count=$(find backups/ -name '*.sql.gz' 2>/dev/null | wc -l)
    if [[ "$backup_count" -gt 5 ]]; then
        info "Cleaning up old backups (keeping last 5)..."
        ls -1t backups/*.sql.gz 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null || true
    fi

    echo ""
    ok "Update complete! Running version: ${target}"
    echo ""
    info "Dashboard:   http${APP_URL:+s}://${APP_URL:-localhost}"
    info "Backend API: http${APP_URL:+s}://${APP_URL:-localhost}:${BACKEND_PORT:-8000}/docs"
    info "View logs:   $COMPOSE_CMD logs -f"
    info "Rollback:     ./scripts/update.sh --rollback"
    echo ""
    warn "If something went wrong, check logs with: $COMPOSE_CMD logs -f"
    warn "To rollback:  ./scripts/update.sh --rollback"
}

# ── Parse arguments ──────────────────────────────────────────────────────────
TARGET_VERSION=""
ACTION=""
INSTANCE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --check)     ACTION=check; shift ;;
        --rollback)  ACTION=rollback; shift ;;
        --list)      ACTION=list; shift ;;
        --instance=*) INSTANCE="${1#*=}"; shift ;;
        -h|--help)
            cat <<HELP
XMR Fund Transparency Suite — update script (archive/release-based).

Downloads release archives from GitHub Releases and redeploys. No git clone or
git binary required — works from a plain extracted archive install.

Usage:
  $(basename "$0")              # Update to latest release
  $(basename "$0") v0.2.0       # Update to a specific version
  $(basename "$0") --check      # Check for available updates
  $(basename "$0") --rollback   # Roll back to previous version
  $(basename "$0") --list        # List available release versions
  $(basename "$0") --instance=NAME  # Operate on a specific instance (reads .env)
  $(basename "$0") -h           # Show this help

The script will:
  1. Create a database backup
  2. Download the release archive from GitHub Releases
  3. Stop containers and swap the application code (preserving .env and data)
  4. Rebuild and restart Docker containers
  5. Wait for the backend health check

Database migrations run automatically on backend startup.

Environment:
  GITHUB_TOKEN   Optional. Raises the GitHub API rate limit if set.

State files (in the app directory):
  .deploy-version   Currently deployed version tag
  .deploy-previous  Version to return to via --rollback
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
        load_env_config
        check_for_updates
        ;;
    list)
        list_versions
        ;;
    rollback)
        check_env
        load_env_config
        do_rollback
        ;;
    update)
        check_env
        load_env_config
        do_update "$TARGET_VERSION"
        ;;
esac
