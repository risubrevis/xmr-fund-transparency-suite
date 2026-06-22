# XMR Fund Transparency Suite

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT">
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white" alt="Docker Ready">
  <img src="https://img.shields.io/badge/Monero-FF6600?logo=monero&logoColor=white" alt="Monero">
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Vue%203-4FC08D?logo=vuedotjs&logoColor=white" alt="Vue 3">
  <img src="https://img.shields.io/badge/TailwindCSS-06B6D4?logo=tailwindcss&logoColor=white" alt="TailwindCSS">
</p>

> Self-hosted, view-only transparency tool for Monero crowdfunding, CCS milestones, and donation tracking with real-time analytics.

---

## Overview & The Problem

Monero is private by design. While this is a strength for everyday users, it creates a serious hurdle for fundraisers, CCS proposal authors, streamers, and NGOs who need to **prove legitimacy** to their communities. Traditionally, demonstrating donation progress meant exposing sensitive wallet credentials — or worse, the **private spend key** — putting every coin at risk.

**XMR Fund Transparency Suite (XMR FTS)** solves this by letting you voluntarily open transparency for a single wallet using only its **private view key** (read-only access) and a **primary/deposit address**.

The application connects to a local `monero-wallet-rpc`, incrementally scans the blockchain, and builds a beautiful public dashboard — all while your funds remain entirely under your control.

### Architecture: One Instance = One Wallet

XMR FTS follows a strict **one instance = one wallet** model.

- Each deployment tracks exactly one `Fund` record. Attempting to create a second fund returns **409 Conflict**.
- This eliminates RPC race conditions (`open_wallet` / `close_wallet`), simplifies the background scanner lifecycle, and makes deployment fully deterministic.
- Need to track multiple wallets? Spin up separate app instances.

---

## Key Features

### 🔒 View-Key Only Security

Your private view key is **never stored in plaintext**. It is encrypted at rest using **AES-256 via Fernet** (`cryptography` library) with a master secret from the `VIEW_KEY_MASTER_SECRET` environment variable. The scanner decrypts it in-memory only during RPC calls, and the key is **never logged**.

### 🎯 Sub-Address Isolation (`deposit_address`)

Each fund exposes an optional `deposit_address` field. When set (for example, a subaddress starting with `8...`), the scanner **filters all incoming transfers** and counts only transactions arriving at that specific address. Personal transfers to the primary address or other subaddresses are silently ignored.

Changing the `deposit_address` automatically resets scan history and triggers a full rescan.

### 📊 Advanced Analytics (4 Charts)

| Chart | Description |
|-------|-------------|
| **Cumulative Received XMR** | Area chart showing total donations over time with Monero-orange gradient fill. |
| **Goal & Progress Tracker** | Interactive toggle between a horizontal progress bar with milestones and a radial gauge for visual fundraising targets. |
| **XMR Volume Distribution** | Bar chart of donation activity across time periods with adjustable range filters. |
| **Donation Size Segmentation** | Donut chart classifying donors into tiers: **Micro** (< 0.1 XMR), **Medium** (0.1–1.0 XMR), **Large** (1.0–5.0 XMR), **Whale** (> 5.0 XMR). |

### 🔍 Data Filtering & Multi-Sorting

The transaction table supports **multi-column sorting** (for example, `timestamp:desc,amount_xmr:asc`) and rich filtering by:

- **Date range** (`start_date`, `end_date`)
- **Amount tiers** (`tiers=micro,medium,large,whale`)

Filter logic lives in a single shared module (`backend/app/filters.py`) and is reused by the paginated list, exports, and public widget.

### 📄 Multi-Format Financial Reports

Download professional reports in **PDF, XLSX, CSV, XML, and JSON** from a unified endpoint:

- **PDF** — Rendered via Jinja2 → HTML → WeasyPrint with a detailed header (actual balance, target balance, filter metadata, last scanned height) and footer calculations.
- **XLSX** — Generated with `openpyxl`.
- **CSV, XML, JSON** — Standard structured formats for accounting integrations.

All exports respect the same filters and sorting as the live transaction table.

### 📢 News Micro-Blog Inside Public Widget

- Manage short fund announcements directly from the admin dashboard.
- Posts are tied to a fund via foreign key with **CASCADE** delete.
- The public embed widget includes a collapsible News section with a **freshness badge** (`+N`) when posts were published within the last 24 hours.
- The widget also renders a **QR code** pointing to the donation address.

### ⚡ Real-Time Updates via SSE

The scanner publishes events to Redis Pub/Sub. The frontend listens to `/api/v1/funds/{id}/events` over **Server-Sent Events** (SSE) with a 30-second heartbeat, updating the dashboard instantly as new donations arrive — no polling required.

---

## Screenshots

### Public Embed Widget

Drop a single `<script>` tag into any website to display live donation progress, a QR code for mobile payments, and a collapsible news feed with freshness indicators.

![Public Widget](assets/Widget_1.png)

### Fund Management Dashboard

The admin dashboard provides real-time analytics, transaction filtering, multi-format exports, and full control over fund settings and widget appearance.

![Admin Dashboard](assets/Dashboard.png)

### All Screenshots

| File | Description |
|------|-------------|
| [Widget_1.png](assets/Widget_1.png) | Public embed widget (blue) |
| [Widget_2.png](assets/Widget_2.png) | Public embed widget (alternative) |
| [Dashboard.png](assets/Dashboard.png) | Fund admin dashboard |
| [Dashboard_Preview.png](assets/Dashboard_Preview.png) | Dashboard preview |
| [Blog_Posts.png](assets/Blog_Posts.png) | News micro-blog management |
| [Embed_Widget_Style_Settings.png](assets/Embed_Widget_Style_Settings.png) | Widget style settings |
| [System_Settings.png](assets/System_Settings.png) | System settings |

---

## Project Architecture

```text
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Browser   │<────>│   FastAPI    │<────>│ PostgreSQL  │
│             │      │   Backend    │      │   Database  │
└─────────────┘      └──────┬───────┘      └─────────────┘
                            │
                            ▼
                   ┌────────────────┐
                   │ monero-wallet- │
                   │     rpc        │
                   └────────────────┘
                            │
                   ┌────────┴────────┐
                   │  Redis (SSE)    │
                   └─────────────────┘
```

| Service | Role |
|---------|------|
| `postgres` | Stores `Fund`, `Transaction`, `Post`, and runtime settings |
| `redis` | Pub/Sub broker for SSE real-time updates |
| `monero-wallet-rpc` | Single view-only RPC wallet (`ghcr.io/sethforprivacy/simple-monero-wallet-rpc`) |
| `backend` | FastAPI app — REST API, auth, reports, widget endpoints |
| `worker` | Background blockchain scanner (`python -m worker.scanner`) |
| `frontend` | Vue 3 SPA built with Vite; served by nginx |

### Directory Structure

```text
xmr-fund-transparency-suite/
├── backend/                    # FastAPI Application
│   ├── app/
│   │   ├── api/v1/endpoints/   # REST routes (funds, transactions, posts, exports, widget, events)
│   │   ├── reports/          # Report generators (pdf.py, xlsx.py, csv_export.py, xml.py, json_export.py)
│   │   ├── models.py         # SQLAlchemy 2.0 models (Fund, Transaction, Post)
│   │   ├── crypto.py         # Fernet AES-256 view-key encryption
│   │   ├── filters.py        # Shared transaction filter/sort logic
│   │   └── rpc_client.py     # monero-wallet-rpc helpers
│   ├── worker/
│   │   └── scanner.py        # Async background blockchain scanner
│   ├── tests/                # pytest suite (auth, crypto, reports, scanner)
│   └── Dockerfile            # Includes pango/cairo deps for WeasyPrint
├── frontend/                   # Vue 3 + Vite + TailwindCSS + Chart.js
│   └── src/
│       ├── pages/            # Dashboard, News, Settings, Widget
│       ├── components/       # Charts, Filters, FundCard, WidgetPreview
│       ├── composables/      # useFund, useSSE, useDatetimeFormat, useTransactionFilters
│       └── stores/
│           └── fund.ts       # Pinia store (API key, current fund, auth)
├── scripts/
│   ├── setup.sh              # One-command deploy / dev / stop / clean
│   ├── update.sh             # Release-based updates with backups and rollback
│   └── test-data.sh          # Seed demo transactions
├── docker-compose.yml          # Unified compose (prod + dev via env override)
├── .env.example                # All configurable environment variables
└── data/
    └── settings.json           # Runtime settings (datetime format, widget colors)
```

---

## Quick Start & Deployment

### Prerequisites

- [Docker](https://docs.docker.com/engine/install/) & [Docker Compose](https://docs.docker.com/compose/install/)
- `openssl` (available on virtually all Linux distributions)
- A Monero wallet with its **private view key** and **primary address**

### Step 1: Clone the Repository

```bash
git clone https://github.com/risubrevis/xmr-fund-transparency-suite.git
cd xmr-fund-transparency-suite
```

### Step 2: Run the Setup Script

```bash
./scripts/setup.sh
```

On the first run, the script will:

1. Auto-generate an `.env` file from `.env.example`
2. Create secure random values for `DB_PASSWORD`, `API_KEY`, and `VIEW_KEY_MASTER_SECRET`
3. Create persistent data directories (`postgres/`, `redis/`, `monero-wallet-rpc/`, `data/`)
4. Start all containers in detached production mode

After completion, the terminal will display your generated **API Key** — save it immediately, as it will not be shown again.

### Step 3: Review Critical Environment Variables

Open `.env` and verify at least these two fields before exposing the instance to the internet:

```bash
ENVIRONMENT=local     # Change to 'production' for live servers
APP_URL=localhost       # Change to your domain (e.g., dashboard.example.com)
```

### Step 4: Open the Dashboard

Navigate to `http://localhost:3000` and log in with your API key.

### Development Mode (Hot Reload)

```bash
./scripts/setup.sh --dev
```

Mounts the backend and worker code into the containers with `uvicorn --reload` and `watchfiles` for instant feedback.

### Other Setup Commands

```bash
./scripts/setup.sh --stop   # Stop all containers
./scripts/setup.sh --clean  # Stop and DELETE all persistent data (interactive confirmation required)
./scripts/setup.sh --init   # Prepare directories only, do not start containers
```

---

## Generating Test Data

To see charts and tables in action before real donations arrive, seed the database with demo transactions:

```bash
# Generate 150 random transactions for a test fund
./scripts/test-data.sh --count=150

# Use with the dev environment
./scripts/test-data.sh --dev --count=100
```

The script creates a test fund if none exists and appends new rows on every run — existing data is never deleted.

---

## Updates & Rollbacks

The `update.sh` script handles zero-downtime updates with automatic database backups.

```bash
# Update to the latest release tag
./scripts/update.sh

# Update to a specific version
./scripts/update.sh v0.2.0

# Check for available updates without applying
./scripts/update.sh --check

# List all available release versions
./scripts/update.sh --list

# Roll back to the previously deployed version
./scripts/update.sh --rollback
```

**What the script does:**

1. Creates a compressed PostgreSQL backup (`backups/*.sql.gz`, last 5 retained)
2. Fetches release tags from GitHub
3. Checks out the target version
4. Rebuilds and restarts Docker containers
5. Waits for the backend health check (Alembic migrations run automatically in `entrypoint.sh`)
6. Records the deployed version in `.deploy-version` for future rollback

---

## Production Reverse Proxy Example

Below is a minimal Nginx `server` block that proxies traffic to the frontend container. It preserves the original host, forwards real client IPs, and supports WebSocket upgrades for Vite HMR in dev mode and SSE connections.

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name dashboard.xmrfts.local;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support — Vite HMR + SSE
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

> **Recommendation:** For production, terminate TLS with a valid SSL certificate (for example, via Let's Encrypt / Certbot) and redirect HTTP to HTTPS.

---

## API Reference

All times are returned in ISO 8601 format unless a custom datetime pattern is configured via `PUT /api/v1/settings/datetime-format`.

### Admin API — Requires `X-API-Key` Header

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/funds` | Create a fund (one per instance; returns 409 if exists) |
| `GET` | `/api/v1/funds` | List funds |
| `GET` | `/api/v1/funds/{id}` | Fund detail + stats (`total_received_xmr`, `transaction_count`, `last_tx_at`) |
| `PATCH` | `/api/v1/funds/{id}` | Update label, description, `is_active`, target, or `deposit_address` |
| `DELETE` | `/api/v1/funds/{id}` | Delete fund, transactions, posts, and close the RPC wallet |
| `GET` | `/api/v1/funds/{id}/txs` | Paginated transactions with date range, tier, and multi-sort filters |
| `GET` | `/api/v1/funds/{id}/report.pdf` | PDF report (WeasyPrint) |
| `GET` | `/api/v1/funds/{id}/report.xml` | XML report |
| `GET` | `/api/v1/funds/{id}/export/{format}` | Unified export: `pdf`, `xlsx`, `csv`, `xml`, `json` (same filters as `/txs`) |
| `GET` | `/api/v1/funds/{id}/events` | SSE real-time stream (30s heartbeat) |
| `POST` | `/api/v1/posts` | Create a news post |
| `PATCH` | `/api/v1/posts/{id}` | Update a post |
| `DELETE` | `/api/v1/posts/{id}` | Delete a post |
| `GET` | `/api/v1/settings/datetime-format` | Get current datetime pattern |
| `PUT` | `/api/v1/settings/datetime-format` | Update datetime pattern |
| `PUT` | `/api/v1/settings/widget-color` | Update widget base color |
| `PUT` | `/api/v1/settings/widget-text-color` | Update widget text color |

### Public API — No Authentication Required

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/posts` | List all posts (newest first) |
| `GET` | `/widget/{uuid}.js` | Embeddable JavaScript widget (QR code + news) |
| `GET` | `/widget/{uuid}.json` | Widget JSON data |
| `GET` | `/widget/{uuid}/posts.json` | Widget posts JSON |
| `GET` | `/widget/{uuid}/export/{format}` | Public widget export (`xml`, `csv`, `json`) |
| `GET` | `/health` | Healthcheck with DB, Redis, RPC, and scanner status |

---

## Environment Variables

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
| `CORS_ORIGINS` | *(empty)* | Additional comma-separated CORS origins |
| `SENTRY_DSN` | *(empty)* | Optional Sentry error tracking DSN |

> **Security note:** Generate `VIEW_KEY_MASTER_SECRET` with `openssl rand -hex 32`. It must be at least 32 bytes.

---

## License

MIT
