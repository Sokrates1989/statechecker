# 📁 Local Deployment

This directory contains Docker Compose files for local development of Statechecker.

## 📋 Compose Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Full stack with API, checker, database, and phpMyAdmin |

## 🚀 Usage

### Start Full Stack

```bash
# From project root
docker compose --env-file .env -f local-deployment/docker-compose.yml up --build
```

### Stop Services

```bash
docker compose --env-file .env -f local-deployment/docker-compose.yml down
```

### View Logs

```bash
docker compose --env-file .env -f local-deployment/docker-compose.yml logs -f
```

## 📝 Configuration

Make sure you have a `.env` file in the project root with:
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `REST_API_PORT`
- Telegram/Email notification settings
- Website/backup check configuration

See `setup/.env.template` for all options.

## 🔗 Endpoints

Once running, the services are available at:
- **API**: `http://localhost:8787` (or your configured `REST_API_PORT`)
- **phpMyAdmin**: `http://localhost:8080`
