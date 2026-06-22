# XMR Fund Transparency Suite

Self-hosted web application for organizations, streamers, CCS campaigns, and NGOs to **publicly display XMR donations** to their wallet **without revealing private spend key**. You only provide a **view key** (read-only access) and get a beautiful dashboard with charts, transaction table, PDF/XML reports, and a public widget for your website.

## Features

- 🔒 **View-key only** — Never expose your spend key
- 📊 **Real-time dashboard** — Track donations as they arrive
- 📈 **Charts & analytics** — Visualize funding progress
- 📄 **PDF/XML reports** — Automated financial reporting
- 🌐 **Public widget** — Embeddable balance display for your website
- 🐳 **Docker-ready** — One-command deployment

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Monero wallet (CLI or GUI)
- Basic command line knowledge

### Step 1: Get Your View Key

```bash
# In monero-wallet-cli
[wallet 4AdUnd...]: export_view_key
Your private view key: abcdef1234567890...
```

**Important:** This is your **private view key**, NOT your spend key. It only allows viewing transactions, not spending.

### Step 2: Clone and Configure

```bash
git clone https://github.com/your-org/xmr-fund-transparency-suite.git
cd xmr-fund-transparency-suite

cp .env.example .env

# Generate secure secrets
openssl rand -hex 32  # For API_KEY
openssl rand -hex 32  # For VIEW_KEY_MASTER_SECRET
```

### Step 3: Edit .env file

```env
DB_PASSWORD=your_secure_db_password
API_KEY=your_api_key_from_step_2
VIEW_KEY_MASTER_SECRET=your_encryption_key_from_step_2
MONERO_RPC_URL=http://monero-wallet-rpc:18082/json_rpc
SCAN_INTERVAL=60
```

### Step 4: Start with Docker

```bash
./scripts/setup.sh
```

For development with hot-reload:

```bash
./scripts/setup.sh --dev
```

### Step 5: Create Your First Fund

```bash
curl -X POST http://localhost:8000/api/v1/funds \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "label": "My CCS Campaign",
    "primary_address": "4AdUndXHHZ9cf2bqQ3P7CF2F9xK2s5f2RMZZU6L5HraAB3Z2TL65E6R4E6T1GtGcY3UphTB2C5sZfrYj7Y52bHvMFbS4fQ",
    "view_key": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
    "start_height": 3280000
  }'
```

### Step 6: Open Dashboard

Navigate to `http://localhost:3000` and see your fund dashboard!

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Browser   │◄────►│   FastAPI    │◄────►│ PostgreSQL  │
│             │      │   Backend    │      │   Database  │
└─────────────┘      └──────┬───────┘      └─────────────┘
                            │
                            ▼
                   ┌────────────────┐
                   │ monero-wallet- │
                   │     rpc        │
                   └────────────────┘
```

**One instance = One wallet**. For multiple wallets, run multiple instances.

## Project Structure

```
xmr-fund-transparency-suite/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # API routes
│   │   ├── reports/             # PDF/XML generation
│   │   ├── auth.py              # API key authentication
│   │   ├── config.py            # Settings (env vars)
│   │   ├── crypto.py            # View key encryption & validation
│   │   ├── database.py          # SQLAlchemy async setup
│   │   ├── logging.py           # Structured logging (structlog)
│   │   ├── main.py              # FastAPI app factory
│   │   ├── models.py            # SQLAlchemy models
│   │   └── schemas.py           # Pydantic schemas
│   ├── alembic/                 # Database migrations
│   ├── worker/
│   │   └── scanner.py           # Background blockchain scanner
│   ├── tests/                   # Test suite
│   ├── Dockerfile                # Backend & worker container
│   └── requirements.txt
├── frontend/                    # Vue 3 + TailwindCSS
├── docker-compose.yml
├── .env.example
└── .github/workflows/ci.yml
```

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/funds` | Create new fund | API Key |
| GET | `/api/v1/funds/{id}` | Get fund status | API Key |
| GET | `/api/v1/funds/{id}/txs` | List transactions | API Key |
| GET | `/api/v1/funds/{id}/report.pdf` | Download PDF report | API Key |
| GET | `/api/v1/funds/{id}/report.xml` | Download XML report | API Key |
| GET | `/api/v1/funds/{id}/events` | SSE stream for real-time updates | API Key |
| PATCH | `/api/v1/funds/{id}` | Update fund settings | API Key |
| DELETE | `/api/v1/funds/{id}` | Delete fund | API Key |
| GET | `/widget/{uuid}.js` | Public widget JavaScript | None |
| GET | `/widget/{uuid}.json` | Public widget JSON data | None |
| GET | `/health` | Healthcheck | None |

## Configuration

All configuration via environment variables in `.env`:

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_PASSWORD` | PostgreSQL password | `changeme` |
| `API_KEY` | Admin API key (64 hex chars) | `openssl rand -hex 32` |
| `VIEW_KEY_MASTER_SECRET` | Encryption key for view keys | `openssl rand -hex 32` |
| `MONERO_RPC_URL` | monero-wallet-rpc URL | `http://rpc:18082/json_rpc` |
| `SCAN_INTERVAL` | Seconds between scans | `60` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Updating

```bash
./scripts/update.sh              # Update to latest release
./scripts/update.sh v0.2.0       # Update to specific version
./scripts/update.sh --check      # Check for available updates
./scripts/update.sh --rollback    # Roll back to previous version
```

The update script automatically:
- Creates a database backup before switching versions
- Fetches the latest release tags from GitHub
- Checks out the target version and rebuilds containers
- Waits for the backend health check (migrations run automatically)

## License

MIT