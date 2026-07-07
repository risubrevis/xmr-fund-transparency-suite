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

## 🌐 Live Production Website

The official landing page and live tracking demonstration of this project is running at **[xmrfts.com](https://xmrfts.com)**.

You can visit the live platform to inspect the open-source analytics integration, view deployment use-cases, and test the embeddable public donation widget running on top of a live Monero node.

---

## ⚡ The Challenge: Crowdfunding in Pure Privacy

Monero is the gold standard for financial privacy. But if you are a developer, streamer, NGO, or the author of a CCS proposal, this absolute privacy becomes your biggest bottleneck:
* **The Trust Gap:** How do you prove to your community that you've actually received 45 XMR out of a 100 XMR goal without making them wait for manual spreadsheet updates?
* **The Security Nightmare:** Sharing wallet screenshots or raw logs is unprofessional, but exposing your **private spend key** just to prove your balance is suicidal — one mistake, and all your funds are gone.
* **The Routine Drain:** Manually tracking incoming donations, verifying hashes for users, and updating progress bars on your website takes hours that should be spent writing code or creating content.

**If your community can't see the progress, momentum dies, and donations dry up.**

---

## 🚀 The Solution: XMR Fund Transparency Suite

**XMR FTS** turns voluntary transparency into a powerful tool to build trust and accelerate your funding goals. By utilizing Monero's native mathematical architecture, it scans the blockchain using **only your private view key**.

Your coins remain 100% secure in cold storage, while your donors get a beautiful, interactive, real-time proof of your fund's life and milestones.

### 🎯 Why use XMR FTS for your next campaign?

* **Eliminate "Donation Hesitation":** When donors see a beautiful, real-time cumulative chart moving toward a milestone, the "FOMO effect" kicks in. They want to be the ones who push the progress bar to 100%.
* **Zero-Maintenance Transparency:** Drop our sleek, responsive widget into your existing website or blog. Once it's there, you never have to manually report a donation again. The suite automatically detects blocks, updates progress, and keeps your community in the loop.
* **Keep Personal Funds Personal:** Built-in **Sub-Address Isolation** means you can generate a specific sub-address (starting with `8...`) for a target campaign (e.g., "Buy me a coffee"). XMR FTS will strictly track that sub-address, completely ignoring your main wallet balance and personal transactions.
* **Professional Audit-Ready Reports:** Generate executive cryptographic summaries or download structured financial sheets (PDF, XLSX, CSV, XML, JSON) with a single click to back up your milestone claims on Reddit, Gitlab, or the Monero CCS platform.
* **Engage Donors Instantly:** Use the built-in microblog to publish code updates or status reports directly inside the public widget. When people come to donate, they don't just see a cold QR code — they see active development and a live 24-hour fresh news counter.

> **Multi-Wallet, Multi-Fund Architecture:** A single XMR FTS instance can manage **multiple view-only wallets**, each containing **multiple funds** with their own deposit sub-addresses. Switch between wallets and funds in the dashboard, give each fund its own branded widget, and let the background scanner handle them all.

---

## Key Features

### 🔒 View-Key Only Security

Your private view key is **never stored in plaintext**. It is encrypted at rest using **AES-256 via Fernet** (`cryptography` library) with a master secret from the `VIEW_KEY_MASTER_SECRET` environment variable. The scanner decrypts it in-memory only during RPC calls, and the key is **never logged**.

### 💼 Multi-Wallet Support

Connect **multiple Monero view-only wallets** to a single XMR FTS instance. Each wallet is independently managed — create, pause, or remove wallets at any time. The background scanner cycles through all active wallets, and the dashboard provides a wallet selector to switch between them.

### 🎯 Sub-Address Isolation (`deposit_address`)

Each fund exposes an optional `deposit_address` field. When set (for example, a subaddress starting with `8...`), the scanner **filters all incoming transfers** and counts only transactions arriving at that specific address. Personal transfers to the primary address or other subaddresses are silently ignored.

Changing the `deposit_address` automatically resets scan history and triggers a full rescan.

### 🎨 Per-Fund Widget Styling

Each fund has its own `widget_background_color` and `widget_text_color`, configurable via the fund settings page. Drop a `<script>` tag into any website to display live donation progress, a QR code, and a collapsible news feed — all branded to match your campaign.

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

The scanner publishes events to Redis Pub/Sub. The frontend listens to `/api/v1/wallets/{id}/events` over **Server-Sent Events** (SSE) with a 30-second heartbeat, updating the dashboard instantly as new donations arrive — no polling required.

---

## Screenshots

### Public Embed Widget

Drop a single `<script>` tag into any website to display live donation progress, a QR code for mobile payments, and a collapsible news feed with freshness indicators.

![Public Widget](assets/Widget_1.png)

### Fund Management Dashboard

The admin dashboard provides real-time analytics, transaction filtering, multi-format exports, and full control over fund settings and widget appearance.

![Admin Dashboard](assets/Dashboard_Preview.png)

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
              ┌─────────────┼──────────────┐
              ▼             ▼               ▼
     ┌──────────────┐ ┌─────────┐  ┌──────────────┐
     │ monero-wallet│ │  Redis  │  │   Worker     │
     │     rpc      │ │ (SSE)   │  │  (scanner)   │
     └──────────────┘ └─────────┘  └──────────────┘
```

| Service | Role |
|---------|------|
| `postgres` | Stores `Wallet`, `Fund`, `Transaction`, `Post`, and runtime settings |
| `redis` | Pub/Sub broker for SSE real-time updates |
| `monero-wallet-rpc` | View-only RPC wallet supporting multiple wallets (`--wallet-dir`) |
| `backend` | FastAPI app — REST API, auth, reports, widget endpoints |
| `worker` | Background blockchain scanner (`python -m worker.scanner`) — scans all active wallets |
| `frontend` | Vue 3 SPA built with Vite; served by nginx |

### Data Model

```text
Wallet 1 ──┬── Fund A (deposit_address: 8abc…) ──┬── Transaction 1
           │                                       └── Transaction 2
           ├── Fund B (deposit_address: 8def…) ──┬── Transaction 3
           │                                       └── Post 1
           └── Fund C (deposit_address: 8ghi…) ──── Post 2

Wallet 2 ──── Fund D (deposit_address: 8jkl…) ── Transaction 4
```

- One **Wallet** holds the view key and represents a Monero view-only wallet on `monero-wallet-rpc`.
- Each **Fund** has a unique `deposit_address` (typically a sub-address) and belongs to one wallet.
- **Transactions** and **Posts** are linked to both a fund and a wallet (with cascade delete).

### Directory Structure

```text
xmr-fund-transparency-suite/
├── backend/                    # FastAPI Application
│   ├── app/
│   │   ├── api/v1/endpoints/   # REST routes (wallets, funds, transactions, posts, exports, widget, events)
│   │   ├── reports/            # Report generators (pdf.py, xlsx.py, csv_export.py, xml.py, json_export.py, png_widget.py)
│   │   ├── models.py           # SQLAlchemy 2.0 models (Wallet, Fund, Transaction, Post)
│   │   ├── schemas.py          # Pydantic v2 schemas (WalletCreate, FundCreate, PostCreate, etc.)
│   │   ├── crypto.py           # Fernet AES-256 view-key encryption
│   │   ├── filters.py          # Shared transaction filter/sort logic
│   │   ├── rpc_client.py       # monero-wallet-rpc helpers (multi-wallet: create, open, get_transfers, close)
│   │   ├── settings.py          # JSON-file runtime settings
│   │   ├── validators.py       # Datetime format & color validation
│   │   └── auth.py              # API key middleware
│   ├── worker/
│   │   └── scanner.py          # Async background blockchain scanner (multi-wallet)
│   ├── tests/                  # pytest suite (auth, crypto, reports, scanner)
│   └── Dockerfile              # Includes pango/cairo deps for WeasyPrint
├── frontend/                   # Vue 3 + Vite + TailwindCSS + Chart.js
│   └── src/
│       ├── pages/              # Dashboard, Wallets, WalletDetail, FundDetail, News, Settings
│       ├── components/         # Charts, Filters, FundCard, WidgetPreview, ColorPicker
│       ├── composables/        # useFund, useSSE, useDatetimeFormat, useChartPreferences, useTransactionFilters
│       └── stores/
│           └── fund.ts         # Pinia store (API key, wallets, funds, auth, SSE)
├── scripts/
│   ├── setup.sh                # One-command deploy / dev / stop / clean
│   ├── update.sh               # Release-based updates with backups and rollback
│   └── test-data.sh            # Seed demo transactions (use --multi for multi-wallet)
├── docker-compose.yml          # Unified compose (prod + dev via env override)
├── .env.example                # All configurable environment variables
└── data/
    └── settings.json           # Runtime settings (datetime format)
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

This launches the **default production instance**. To deploy an isolated demo or staging instance alongside production, see [Multi-Instance Deployment](#multi-instance-deployment) below.

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

Navigate to `http://localhost:3000` and log in with your API key. From the dashboard you can:

1. **Create a wallet** — provide your Monero primary address and private view key
2. **Create funds** — each fund has its own deposit sub-address and fundraising target
3. **Customize widget** — each fund has its own colors, description, and public website

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
./scripts/setup.sh --instance=demo   # Deploy as the demo instance (shifted ports)
./scripts/setup.sh --instance=staging # Deploy as the staging instance
```

---

## Generating Test Data

To see charts and tables in action before real donations arrive, seed the database with demo transactions:

```bash
# Generate 150 random transactions for a test fund
./scripts/test-data.sh --count=150

# Use with the dev environment
./scripts/test-data.sh --dev --count=100

# Seed multi-wallet demo data (3 wallets × 2 funds + transactions)
./scripts/test-data.sh --multi
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

## Multi-Instance Deployment

Multiple isolated instances (production, demo, staging, etc.) can run on the **same host** without port or container-name collisions. Each instance lives in its own directory with its own `.env`, Docker Compose project name, host ports, and data volumes.

### How It Works

The `--instance=NAME` flag tells `setup.sh` to generate a `.env` with a unique `COMPOSE_PROJECT_NAME` and a preset of non-overlapping host ports:

| Instance | Project name | Frontend | Backend | Postgres | Redis | Monero RPC | APP_URL | Environment |
|----------|-------------|----------|---------|----------|-------|------------|---------|-------------|
| `prod` (default) | `xmrfts-prod` | 3000 | 8000 | 5432 | 6379 | 18082 | `dashboard.xmrfts.com` | production |
| `demo` | `xmrfts-demo` | 3001 | 8001 | 5433 | 6380 | 18083 | `demo.xmrfts.com` | production |
| `staging` | `xmrfts-staging` | 3002 | 8002 | 5434 | 6381 | 18084 | `staging.xmrfts.com` | staging |
| custom | `xmrfts-{name}` | 3000 | 8000 | 5432 | 6379 | 18082 | `localhost` | production |

For custom instance names, prod port defaults are used and the script prints a warning — edit `.env` to set unique host ports before starting alongside other instances.

### Isolation Guarantees

| Resource | Mechanism |
|----------|----------|
| **Container names** | `COMPOSE_PROJECT_NAME` prefix — each instance gets unique names (`xmrfts-prod-backend-1` vs `xmrfts-demo-backend-1`) |
| **Docker networks** | Compose creates a separate bridge network per project — no cross-talk by service name |
| **Host ports** | `FRONTEND_PORT`, `BACKEND_PORT`, `POSTGRES_PORT`, `REDIS_PORT`, `MONERO_RPC_PORT` — each instance uses a unique set |
| **Data volumes** | Bind-mounts (`./postgres`, `./redis`, `./monero-wallet-rpc`, `./data`) are relative to each instance directory |
| **Secrets** | Each instance has its own `.env` with independently generated `DB_PASSWORD`, `API_KEY`, `VIEW_KEY_MASTER_SECRET` |
| **Database** | Each instance runs its own PostgreSQL container with a separate data directory |
| **Git state** | Each instance is a separate clone — `update.sh` updates or rolls back each independently |

### Example: Production + Demo on One Server

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

### Updating a Specific Instance

`update.sh` reads `COMPOSE_PROJECT_NAME` and `BACKEND_PORT` from `.env`, so it automatically targets the correct instance:

```bash
cd /home/user/demo.xmrfts.com
./scripts/update.sh --instance=demo
```

### Nginx for Multiple Instances

Each instance needs its own nginx `server` block pointing to its host ports. Production-grade configs with TLS 1.3, security headers, SSE support, and separate rate-limit zones are provided in the [docs repository](https://github.com/risubrevis/xmr-fund-transparency-suite-docs):

| Domain | Frontend | Backend | Config file |
|--------|----------|--------|-------------|
| `dashboard.xmrfts.com` | `127.0.0.1:3000` | `127.0.0.1:8000` | `dashboard.xmrfts.com.nginx.conf` |
| `demo.xmrfts.com` | `127.0.0.1:3001` | `127.0.0.1:8001` | `demo.xmrfts.com.nginx.conf` |
| `staging.xmrfts.com` | `127.0.0.1:3002` | `127.0.0.1:8002` | *(create by analogy)* |

Demo uses separate rate-limit zones (`api_limit_demo`, `sse_limit_demo`, `export_limit_demo`) so its traffic cannot exhaust the production rate-limit buckets. These zones must be added to `/etc/nginx/conf.d/rate_limiting.conf` (see `rate_limiting.nginx..conf` in the docs repo).

---

## API Reference

All times are returned in ISO 8601 format unless a custom datetime pattern is configured via `PUT /api/v1/settings/datetime-format`.

### Admin API — Requires `X-API-Key` Header

#### Wallets

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/wallets` | Create a view-only wallet (address + view key + start height) |
| `GET` | `/api/v1/wallets` | List all wallets |
| `GET` | `/api/v1/wallets/{id}` | Wallet detail |
| `PATCH` | `/api/v1/wallets/{id}` | Update wallet name or active status |
| `DELETE` | `/api/v1/wallets/{id}` | Delete wallet + all its funds, transactions, and posts; close on RPC |

#### Funds

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/funds` | Create a fund linked to a wallet |
| `GET` | `/api/v1/funds` | List funds (optionally filter by `wallet_id`) |
| `GET` | `/api/v1/funds/{id}` | Fund detail + stats (`total_received_xmr`, `transaction_count`, `last_tx_at`) |
| `PATCH` | `/api/v1/funds/{id}` | Update label, description, `is_active`, target, `deposit_address`, widget colors, public website |
| `DELETE` | `/api/v1/funds/{id}` | Delete fund + its transactions and posts |

#### Transactions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/funds/{id}/txs` | Paginated transactions for a fund (date range, tier, multi-sort, cursor) |
| `GET` | `/api/v1/wallets/{id}/txs` | Paginated transactions for a wallet across all its funds (optional `fund_id` filter) |

#### Exports & Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/funds/{id}/export/{format}` | Unified export: `pdf`, `xlsx`, `csv`, `xml`, `json` (same filters as `/txs`) |
| `GET` | `/api/v1/funds/{id}/report.pdf` | PDF report (WeasyPrint) |
| `GET` | `/api/v1/funds/{id}/report.xml` | XML report |
| `GET` | `/api/v1/funds/{id}/widget-png` | Download widget as PNG image (`format` query: `business_card`, `wide`, `vertical`) |

#### Real-Time & Posts

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/wallets/{id}/events` | SSE real-time stream for wallet scan updates (30s heartbeat) |
| `POST` | `/api/v1/posts` | Create a news post (requires `fund_id`) |
| `PATCH` | `/api/v1/posts/{id}` | Update a post (body and/or move to another fund) |
| `DELETE` | `/api/v1/posts/{id}` | Delete a post |

#### Settings

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/settings/datetime-format` | Get current datetime pattern |
| `PUT` | `/api/v1/settings/datetime-format` | Update datetime pattern |

### Public API — No Authentication Required

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/posts` | List posts (filter by `fund_id`, `wallet_id`, `start_date`, `end_date`) |
| `GET` | `/api/v1/wallets/{id}/posts` | List all posts for a wallet across its funds |
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
| `COMPOSE_PROJECT_NAME` | `xmrfts-prod` | Docker Compose project name — instance isolation (see [Multi-Instance Deployment](#multi-instance-deployment)) |
| `FRONTEND_PORT` | `3000` | Host port for the frontend container |
| `BACKEND_PORT` | `8000` | Host port for the backend container |
| `POSTGRES_PORT` | `5432` | Host port for PostgreSQL |
| `REDIS_PORT` | `6379` | Host port for Redis |
| `MONERO_RPC_PORT` | `18082` | Host port for `monero-wallet-rpc` |
| `CORS_ORIGINS` | *(empty)* | Additional comma-separated CORS origins |
| `SENTRY_DSN` | *(empty)* | Optional Sentry error tracking DSN |

> **Security note:** Generate `VIEW_KEY_MASTER_SECRET` with `openssl rand -hex 32`. It must be at least 32 bytes.

---

## ☕ Support & Donations

If **XMR Fund Transparency Suite** helped you build trust with your community or made your CCS campaign a little more transparent, consider sending some crypto-dust to support the developer. Every satoshi, gwei, and piconero keeps the code clean and the commits smooth!

| Coin | Network | Address |
|------|---------|---------|
| **Monero** | XMR | `89tK9E9LbwdCsnnZGFMJzU7yBRGaQ7hfPTeNXWCe2LW3G7kCkJWswhb2ieBkHFrBs2JfdsmumQ3nY9obQ6fxb4HzHpTjCjd` |
| **Bitcoin** | BTC | `bc1qh0t2u7d7u0pl2yzmxuq80verhlfxuj0r29lfv7` |
| **USDT** | Polygon | `0xe1aAE089F1b0A3b2649017A7E7afa720877409C8` |
| **USDC** | Polygon | `0xe1aAE089F1b0A3b2649017A7E7afa720877409C8` |
| **USDT** | TRON | `TMkxXPuxamSci19rSygy58QRjZ9vmLjqtu` |
| **Ethereum** | Arbitrum | `0xe1aAE089F1b0A3b2649017A7E7afa720877409C8` |

---

<div align="center">

**[Report Bug](https://github.com/risubrevis/xmr-fund-transparency-suite/issues) · [Request Feature](https://github.com/risubrevis/xmr-fund-transparency-suite/issues) · [Releases](https://github.com/risubrevis/xmr-fund-transparency-suite/releases)**

</div>

---

## License

MIT
