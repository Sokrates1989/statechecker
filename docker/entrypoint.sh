#!/bin/sh
set -e

# Generate config.txt from environment variables if needed
if [ -f "/code/docker/generate_config_from_env.py" ]; then
    python /code/docker/generate_config_from_env.py
fi

# Generate keycloak-config.js for the website served by the API at /admin
KEYCLOAK_CONFIG_FILE="/code/website/keycloak-config.js"
if [ -d "/code/website" ]; then
    cat > "$KEYCLOAK_CONFIG_FILE" << EOF
/**
 * Keycloak Configuration (auto-generated at container startup)
 */
window.KEYCLOAK_ENABLED = ${KEYCLOAK_ENABLED:-false};
window.KEYCLOAK_URL = '${KEYCLOAK_URL:-http://localhost:9090}';
window.KEYCLOAK_REALM = '${KEYCLOAK_REALM:-statechecker}';
window.KEYCLOAK_CLIENT_ID = '${KEYCLOAK_CLIENT_ID:-statechecker-frontend}';
EOF
    echo "[keycloak-config] Generated $KEYCLOAK_CONFIG_FILE with KEYCLOAK_ENABLED=${KEYCLOAK_ENABLED:-false}"

    # Generate web-version.json for the website served by the API at /admin
    WEB_VERSION_FILE="/code/website/web-version.json"
    cat > "$WEB_VERSION_FILE" << EOF
{"version":"${IMAGE_TAG:-dev}","title":"Statechecker Web"}
EOF
    echo "[web-version] Generated $WEB_VERSION_FILE with version=${IMAGE_TAG:-dev}"
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
