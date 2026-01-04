#!/bin/sh
set -e

# Generate config.txt from environment variables if needed
if [ -f "/code/docker/generate_config_from_env.py" ]; then
    python /code/docker/generate_config_from_env.py
fi

# If database connection details are provided, wait for DB to be reachable
if [ -n "${DB_HOST}" ]; then
    DB_PORT="${DB_PORT:-3306}"
    DB_WAIT_TIMEOUT="${DB_WAIT_TIMEOUT:-60}"

    if [ -f "/code/docker/wait-for-it.sh" ]; then
        exec /code/docker/wait-for-it.sh "${DB_HOST}:${DB_PORT}" -s -t "${DB_WAIT_TIMEOUT}" -- "$@"
    fi
fi

# Hand off to the actual container command (defined in docker-compose)
exec "$@"
