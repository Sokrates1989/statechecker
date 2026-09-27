# 🚀 statechecker README

Primary application repository for the **statechecker** system.

It contains:

- **API** (FastAPI): endpoints used by `stateChecker-client`
- **Worker**: periodic checks for tools/websites/backups
- **Web UI**: authenticated administration and monitoring interface from `website/`
- **MySQL** database schema and local Docker Compose setup

The checker persists each website's latest Up/Down state independently of
notification delivery. With Telegram enabled, DOWN and UP AGAIN alerts remain
pending until at least one configured error chat accepts the message. Partial
delivery is logged and acknowledged after one success, because the database
stores one flag per monitored item. Email error messages are sent after that
acknowledgement, avoiding repeated email during Telegram outages. With
Telegram disabled, the existing email-only behavior remains.

The Web UI's **Notifications** tab shows the server-configured Telegram error
and info chat IDs and sends a test message to either group. Sending requires
`statechecker:admin`; reading the settings requires `statechecker:read` or
`statechecker:admin`. The bot token remains a server-side secret. The API needs
the same Telegram secret and recipient environment settings as the checker.

<br>

## Table of Contents

1. [📖 Overview](#overview)
2. [🧑‍💻 Usage](#usage)
3. [🛠️ Installation & Setup](#installation--setup)
4. [🧠 Configuration](#configuration)
5. [🐞 Troubleshooting](#troubleshooting)
6. [🚀 Summary](#summary)

<br>

# 📖 Overview

The server stores tool state in MySQL and provides endpoints for the client:

- `POST /v1/statecheck`
- `POST /v1/backupcheck`
- `POST /v1/statecheck/stop`
- `POST /v1/backupcheck/stop`

For health checks:

- `GET /health`

For **Docker Swarm deployment**, use the separate repo:

- `swarm/swarm-statechecker`

Repository responsibilities:

- **`statechecker`**: canonical application source for the API, checker worker, web UI, and database schema.
- **`stateChecker-client`**: companion heartbeat client used by monitored tools.
- **`swarm-statechecker`**: Docker Swarm configuration, setup, and deployment tooling.

<br>
<br>

# 🧑‍💻 Usage

```bash
# Start local stack (from repo root)
docker compose --env-file .env -f local-deployment/docker-compose.yml up --build
```

Endpoints:

- **API**: `http://localhost:8787` (or your configured `REST_API_PORT`)
- **Health**: `http://localhost:8787/health`
- **phpMyAdmin**: `http://localhost:8080` (or `PHPMYADMIN_PORT`)

<br>
<br>

# 🛠️ Installation & Setup

## 📌 Requirements

- Docker + Docker Compose
- (Optional) Python for running scripts locally

## 📌 Quick start

```powershell
# Windows
.\quick-start.ps1
```

```bash
# Linux/Mac
./quick-start.sh
```

<br>
<br>

# 🧠 Configuration

## 📌 `.env`

Local compose uses `.env` in the repo root.

Relevant variables:

- `REST_API_PORT`
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `DB_WAIT_TIMEOUT` (seconds to wait for DB on container startup)
- `SERVER_AUTHENTICATION_TOKEN`

## 📌 Server config

The server can load its config via:

- `config.txt` (generated from `config.txt.template` by the entrypoint when needed)
- `STATECHECKER_SERVER_CONFIG` (JSON string)

Google Drive credentials are **optional**.

<br>
<br>

# 🐞 Troubleshooting

## 🧩 EntryPoint “no such file or directory”

If you see `exec /code/docker/entrypoint.sh: no such file or directory` on Windows, ensure:

- The entrypoint is executed via `sh` (avoids CRLF/shebang issues)
- The Docker build normalizes line endings

## 🧩 Database schema issues

If the worker complains about missing tables, reset the local DB via the quick-start menu option:

- `DB Re-Install`

The DB reinstall will:

- Move `db_data/` to `db_data__backup_<timestamp>/` (no auto-delete)
- Re-initialize the DB using either:
  - `install/database/state_checker.sql` (schema-only), or
  - a selected `install/database/backup_*.sql` (optional)

<br>
<br>

# 🚀 Summary

✅ **Local stack** runs via Docker Compose (API + Worker + MySQL + phpMyAdmin).

✅ **API health endpoint** is available at `/health`.

✅ **Swarm deployment** is handled via `swarm/swarm-statechecker`.
