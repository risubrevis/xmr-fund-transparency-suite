#!/bin/bash
# Generate a full set of test data for the XMR Fund Transparency Suite.
#
# Running this script:
#   1. Wipes the database (wallets, funds, giveaways, transactions, posts).
#   2. Creates several wallets.
#   3. In each wallet: several funds AND several giveaways (covering all
#      lifecycle states — ended / closed / active / future).
#   4. Adds several news posts to every fund and every giveaway.
#   5. Adds transactions to funds (never exceeding the fund's target) and to
#      giveaways (respecting min_amount and the start/end date window).
#
# Usage:
#   ./scripts/test-data.sh
#
# NOTE: this DESTROYS all existing data. It is intended for development/demo
# environments only.

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

COMPOSE="docker compose"

info "Generating full test dataset (wipes the database first)..."
$COMPOSE exec -T backend python -m tests.seed_all

ok "Done!"