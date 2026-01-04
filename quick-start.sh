#!/bin/bash
#
# quick-start.sh
#
# Quick start tool for Statechecker:
# 1. Checks Docker installation
# 2. Creates .env from template if needed
# 3. Provides menu for common operations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SETUP_DIR="${SCRIPT_DIR}/setup"

# Source modules
source "${SETUP_DIR}/modules/docker_helpers.sh"
source "${SETUP_DIR}/modules/db_helpers.sh"
source "${SETUP_DIR}/modules/browser_helpers.sh"
source "${SETUP_DIR}/modules/menu_handlers.sh"

echo "🔍 Statechecker - Quick Start"
echo "=============================="
echo ""

# Docker availability check
if ! check_docker_installation; then
    exit 1
fi
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found"
    echo ""
    if [ -f setup/.env.template ]; then
        read -p "Create .env from template? (Y/n): " create_env
        if [[ ! "$create_env" =~ ^[Nn]$ ]]; then
            cp setup/.env.template .env
            echo "✅ .env created from template"
            echo "⚠️  Please edit .env with your configuration before continuing"
            echo ""

            EDITOR_CMD="${EDITOR:-nano}"
            if ! command -v "$EDITOR_CMD" >/dev/null 2>&1; then
                EDITOR_CMD="vi"
            fi
            read -p "Open .env now in $EDITOR_CMD? (Y/n): " open_env
            if [[ ! "$open_env" =~ ^[Nn]$ ]]; then
                "$EDITOR_CMD" .env
            fi

            read -p "Press Enter to continue after editing .env..."
        else
            echo "❌ Cannot continue without .env file"
            exit 1
        fi
    else
        echo "❌ setup/.env.template not found!"
        exit 1
    fi
    echo ""
fi

# Determine compose file
COMPOSE_FILE="local-deployment/docker-compose.yml"

if [ ! -f "$COMPOSE_FILE" ]; then
    echo "⚠️  $COMPOSE_FILE not found"
fi

echo "📋 Using compose file: $COMPOSE_FILE"
echo ""

# Only prompt for DB init on first setup (empty db_data)
if [ "$COMPOSE_FILE" = "local-deployment/docker-compose.yml" ]; then
    if is_db_data_empty; then
        DB_INIT_SOURCE=$(prompt_db_init_mode "$SCRIPT_DIR")
        apply_db_init_source "$COMPOSE_FILE" "$DB_INIT_SOURCE" "state_checker.sql"
        echo ""
    fi
fi

# Show main menu
show_main_menu "$COMPOSE_FILE"
