# API Reference

All times are returned in ISO 8601 format unless a custom datetime pattern is configured via `PUT /api/v1/settings/datetime-format`.

## Admin API — Requires `X-API-Key` Header

### Wallets

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/wallets` | Create a view-only wallet (address + view key + start height) |
| `GET` | `/api/v1/wallets` | List all wallets |
| `GET` | `/api/v1/wallets/{id}` | Wallet detail |
| `PATCH` | `/api/v1/wallets/{id}` | Update wallet name or active status |
| `DELETE` | `/api/v1/wallets/{id}` | Delete wallet + all its funds, transactions, and posts; close on RPC |

### Funds

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/funds` | Create a fund linked to a wallet |
| `GET` | `/api/v1/funds` | List funds (optionally filter by `wallet_id`) |
| `GET` | `/api/v1/funds/{id}` | Fund detail + stats (`total_received_xmr`, `transaction_count`, `last_tx_at`) |
| `PATCH` | `/api/v1/funds/{id}` | Update label, description, `is_active`, target, `deposit_address`, widget colors, public website |
| `DELETE` | `/api/v1/funds/{id}` | Delete fund + its transactions and posts |

### Transactions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/funds/{id}/txs` | Paginated transactions for a fund (date range, tier, multi-sort, cursor) |
| `GET` | `/api/v1/wallets/{id}/txs` | Paginated transactions for a wallet across all its funds (optional `fund_id` filter) |

### Exports & Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/funds/{id}/export/{format}` | Unified export: `pdf`, `xlsx`, `csv`, `xml`, `json` (same filters as `/txs`) |
| `GET` | `/api/v1/funds/{id}/report.pdf` | PDF report (WeasyPrint) |
| `GET` | `/api/v1/funds/{id}/report.xml` | XML report |
| `GET` | `/api/v1/funds/{id}/widget-png` | Download widget as PNG image (`format` query: `business_card`, `wide`, `vertical`) |

### Real-Time & Posts

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/wallets/{id}/events` | SSE real-time stream for wallet scan updates (30s heartbeat) |
| `POST` | `/api/v1/posts` | Create a news post (requires `fund_id`) |
| `PATCH` | `/api/v1/posts/{id}` | Update a post (body and/or move to another fund) |
| `DELETE` | `/api/v1/posts/{id}` | Delete a post |

### Settings

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/settings/datetime-format` | Get current datetime pattern |
| `PUT` | `/api/v1/settings/datetime-format` | Update datetime pattern |

## Public API — No Authentication Required

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/posts` | List posts (filter by `fund_id`, `wallet_id`, `start_date`, `end_date`) |
| `GET` | `/api/v1/wallets/{id}/posts` | List all posts for a wallet across its funds |
| `GET` | `/widget/{uuid}.js` | Embeddable JavaScript widget (QR code + news) |
| `GET` | `/widget/{uuid}.json` | Widget JSON data |
| `GET` | `/widget/{uuid}/posts.json` | Widget posts JSON |
| `GET` | `/widget/{uuid}/export/{format}` | Public widget export (`xml`, `csv`, `json`) |
| `GET` | `/health` | Healthcheck with DB, Redis, RPC, and scanner status |