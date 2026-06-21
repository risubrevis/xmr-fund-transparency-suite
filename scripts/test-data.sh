#!/bin/bash
# Generate test transactions for the XMR Fund Transparency Suite.
#
# Creates a test fund (if none exists) and fills the transactions table
# with random data.  On repeated runs new rows are appended — existing
# data is never deleted.
#
# Usage:
#   ./scripts/test-data.sh                # 50 transactions (default)
#   ./scripts/test-data.sh --count=200    # 200 transactions
#   ./scripts/test-data.sh --dev         # Use dev environment
#   ./scripts/test-data.sh --dev --count=100

set -euo pipefail
cd "$(dirname "$0")/.."

# ── Colors ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}→${NC} $*"; }
ok()    { echo -e "${GREEN}✓${NC} $*"; }
error() { echo -e "${RED}✗${NC} $*"; }

# ── Defaults ────────────────────────────────────────────────────────────────
COUNT=50
DEV=false

# ── Parse arguments ─────────────────────────────────────────────────────────
for arg in "$@"; do
    case "$arg" in
        --count=*)
            COUNT="${arg#*=}"
            ;;
        --dev)
            DEV=true
            ;;
        -h|--help)
            cat <<HELP
Generate test transactions for the XMR Fund Transparency Suite.

Usage:
  $(basename "$0") [OPTIONS]

Options:
  --count=N   Number of transactions to generate (default: 50)
  --dev       Use dev environment (INSTALL_DEV=true)
  -h          Show this help
HELP
            exit 0
            ;;
        *)
            error "Unknown option: $arg"
            exit 1
            ;;
    esac
done

# ── Select compose mode ──────────────────────────────────────────────────
if [[ "$DEV" == true ]]; then
    export INSTALL_DEV=true
    COMPOSE="docker compose"
else
    COMPOSE="docker compose"
fi

# ── Step 1: Ensure a test fund exists ───────────────────────────────────────
info "Seeding test fund..."
FUND_ID=$($COMPOSE exec -T backend python -m tests.create_test_fund)

if [ -z "$FUND_ID" ]; then
    error "No funds found in database. Create a fund first or check database connectivity."
    exit 1
fi

ok "Using fund: $FUND_ID"

# ── Step 2: Generate random transactions ────────────────────────────────────
info "Generating $COUNT random transactions..."
$COMPOSE exec -T backend python -m tests.create_test_transactions --count="$COUNT" --fund-id="$FUND_ID"

ok "Done!"
