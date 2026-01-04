# 📁 Local Deployment README

Local Docker Compose setup for `python/statechecker`.

<br>

## Table of Contents

1. [📖 Overview](#overview)
2. [🧑‍💻 Usage](#usage)
3. [🛠️ Configuration / Installation / Setup](#configuration--installation--setup)
4. [🔗 Endpoints](#endpoints)
5. [🚀 Summary](#summary)

<br>

# 📖 Overview

`docker-compose.yml` runs:

- **api** (FastAPI)
- **check** (worker)
- **db** (MySQL)
- **phpmyadmin** (optional)

<br>
<br>

# 🧑‍💻 Usage

```bash
# From repository root
docker compose --env-file .env -f local-deployment/docker-compose.yml up --build

# Stop
docker compose --env-file .env -f local-deployment/docker-compose.yml down

# Logs
docker compose --env-file .env -f local-deployment/docker-compose.yml logs -f
```

<br>
<br>

# 🛠️ Configuration / Installation / Setup

Ensure you have a `.env` file in the project root.

Relevant variables:

- `REST_API_PORT`
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `DB_WAIT_TIMEOUT` (seconds to wait for DB on container startup)
- `SERVER_AUTHENTICATION_TOKEN`

See `setup/.env.template` for the full list.

Database initialization:

- Default: schema-only init via `install/database/state_checker.sql`
- Optional: restore from a `install/database/backup_*.sql` file (select via quick-start and re-install)

<br>
<br>

# 🔗 Endpoints

- **API**: `http://localhost:8787` (or `REST_API_PORT`)
- **Health**: `http://localhost:8787/health`
- **phpMyAdmin**: `http://localhost:8080` (or `PHPMYADMIN_PORT`)

<br>
<br>

# 🚀 Summary

✅ This folder provides the local Docker Compose stack for development.

✅ Use the repo root `.env` + `local-deployment/docker-compose.yml`.
