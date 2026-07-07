# Quick Start & Deployment

## Prerequisites

- [Docker](https://docs.docker.com/engine/install/) & [Docker Compose](https://docs.docker.com/compose/install/)
- `openssl` (available on virtually all Linux distributions)
- A Monero wallet with its **private view key** and **primary address**

## Step 1: Clone the Repository

```bash
git clone https://github.com/risubrevis/xmr-fund-transparency-suite.git
cd xmr-fund-transparency-suite
```

## Step 2: Run the Setup Script

```bash
./scripts/setup.sh
```

This launches the **default production instance**. To deploy an isolated demo or staging instance alongside production, see [Multi-Instance Deployment](./multi-instance.md).

On the first run, the script will:

1. Auto-generate an `.env` file from `.env.example`
2. Create secure random values for `DB_PASSWORD`, `API_KEY`, and `VIEW_KEY_MASTER_SECRET`
3. Create persistent data directories (`postgres/`, `redis/`, `monero-wallet-rpc/`, `data/`)
4. Start all containers in detached production mode

After completion, the terminal will display your generated **API Key** — save it immediately, as it will not be shown again.

## Step 3: Review Critical Environment Variables

Open `.env` and verify at least these two fields before exposing the instance to the internet:

```bash
ENVIRONMENT=local     # Change to 'production' for live servers
APP_URL=localhost       # Change to your domain (e.g., dashboard.example.com)
```

See [Environment Variables](./environment-variables.md) for the full reference.

## Step 4: Open the Dashboard

Navigate to `http://localhost:3000` and log in with your API key. From the dashboard you can:

1. **Create a wallet** — provide your Monero primary address and private view key
2. **Create funds** — each fund has its own deposit sub-address and fundraising target
3. **Customize widget** — each fund has its own colors, description, and public website

## Development Mode (Hot Reload)

```bash
./scripts/setup.sh --dev
```

Mounts the backend and worker code into the containers with `uvicorn --reload` and `watchfiles` for instant feedback.

## Other Setup Commands

```bash
./scripts/setup.sh --stop   # Stop all containers
./scripts/setup.sh --clean  # Stop and DELETE all persistent data (interactive confirmation required)
./scripts/setup.sh --init   # Prepare directories only, do not start containers
./scripts/setup.sh --instance=demo   # Deploy as the demo instance (shifted ports)
./scripts/setup.sh --instance=staging # Deploy as the staging instance
```