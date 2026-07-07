# Project Architecture

## Overview

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

## Data Model

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

## Directory Structure

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