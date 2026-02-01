#!/bin/bash
#
# menu_stack.sh
#
# Stack operations module for Statechecker quick-start menu.
# This module provides functions for starting, stopping, and managing
# the Docker Compose stack for Statechecker.
#
# Author: Auto-generated
# Date: 2026-01-29
# Version: 1.0.0

MENU_STACK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${MENU_STACK_DIR}/browser_helpers.sh" ]; then
    source "${MENU_STACK_DIR}/browser_helpers.sh"
fi

handle_stack_start() {
    # Start the local stack in foreground.
    #
    # Args:
    #   $1: compose_file - Path to the Docker Compose file.
    local compose_file="$1"
    
    echo "🚀 Starting Statechecker stack..."
    echo ""
    if command -v show_relevant_pages_delayed >/dev/null 2>&1; then
        show_relevant_pages_delayed "$compose_file" 120
    fi
    docker compose --env-file .env -f "$compose_file" up --build
}

handle_stack_start_detached() {
    # Start the local stack detached.
    #
    # Args:
    #   $1: compose_file - Path to the Docker Compose file.
    local compose_file="$1"
    
    echo "🚀 Starting Statechecker stack (detached)..."
    echo ""
    if command -v show_relevant_pages_delayed >/dev/null 2>&1; then
        show_relevant_pages_delayed "$compose_file" 120
    fi
    docker compose --env-file .env -f "$compose_file" up --build -d
    echo ""
    echo "✅ Services started in background"
    echo "📋 View logs with: docker compose --env-file .env -f $compose_file logs -f"
}

handle_stack_start_with_telegram() {
    # Start the local stack in foreground including the Telegram admin bot listener.
    #
    # Args:
    #   $1: compose_file - Path to the Docker Compose file.
    local compose_file="$1"

    echo "🚀 Starting Statechecker stack (with telegram listener)..."
    echo ""
    if command -v show_relevant_pages_delayed >/dev/null 2>&1; then
        show_relevant_pages_delayed "$compose_file" 120
    fi
    docker compose --env-file .env -f "$compose_file" --profile telegram up --build
}

handle_stack_start_with_telegram_and_web() {
    # Start the local stack in foreground including Telegram admin bot listener and nginx web.
    # Uses docker compose logs -f in background to capture container logs to file.
    #
    # Args:
    #   $1: compose_file - Path to the Docker Compose file.
    #   $2: log_to_file - Optional: "true" to log container logs to file.
    local compose_file="$1"
    local log_to_file="${2:-false}"

    echo "🚀 Starting Statechecker stack (with telegram listener + web)..."
    echo ""

    local project_root
    project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    local env_file_path
    env_file_path="$(cd "$project_root" && pwd)/.env"

    local compose_log_file=""
    local log_pid=""

    if [ "$log_to_file" = "true" ]; then
        local timestamp
        timestamp=$(date +%Y%m%d_%H%M%S)
        local log_dir="$project_root/logs/stack/$timestamp"
        mkdir -p "$log_dir"
        compose_log_file="$log_dir/docker-compose.log"
        : > "$compose_log_file"
        echo "📋 Writing docker-compose container logs to: $compose_log_file"
    fi

    if command -v show_relevant_pages_delayed >/dev/null 2>&1; then
        show_relevant_pages_delayed "$compose_file" 120
    fi

    local compose_args=(
        "--ansi" "never"
        "--progress" "plain"
        "--env-file" "$env_file_path"
        "-f" "$compose_file"
        "--profile" "telegram"
        "--profile" "web"
    )

    if [ "$log_to_file" = "true" ]; then
        # Start background job to capture container logs via docker compose logs -f
        (
            cd "$project_root" || exit 1
            echo "[$(date)] docker compose logs -f started" >> "$compose_log_file"
            
            # Wait for at least one container to be running
            local deadline=$(($(date +%s) + 60))
            while [ "$(date +%s)" -lt "$deadline" ]; do
                local running
                running=$(docker compose "${compose_args[@]}" ps --services --filter status=running 2>/dev/null)
                if [ -n "$running" ]; then
                    break
                fi
                sleep 1
            done
            
            # Stream container logs to file
            docker compose "${compose_args[@]}" logs -f --no-color >> "$compose_log_file" 2>&1
            echo "[$(date)] docker compose logs -f stopped" >> "$compose_log_file"
        ) &
        log_pid=$!

        # Run docker compose up (blocks until stopped)
        cd "$project_root" || return 1
        docker compose "${compose_args[@]}" up --build --watch

        # Cleanup background log process
        if [ -n "$log_pid" ]; then
            kill "$log_pid" 2>/dev/null || true
            wait "$log_pid" 2>/dev/null || true
        fi
    else
        docker compose --env-file .env -f "$compose_file" --profile telegram --profile web up --build
    fi
}

handle_stack_start_detached_with_telegram() {
    # Start the local stack in detached mode including the Telegram admin bot listener.
    #
    # Args:
    #   $1: compose_file - Path to the Docker Compose file.
    local compose_file="$1"

    echo "🚀 Starting Statechecker stack (detached, with telegram listener)..."
    echo ""
    if command -v show_relevant_pages_delayed >/dev/null 2>&1; then
        show_relevant_pages_delayed "$compose_file" 120
    fi
    docker compose --env-file .env -f "$compose_file" --profile telegram up --build -d
    echo ""
    echo "✅ Services started in background"
    echo "📋 View logs with: docker compose --env-file .env -f $compose_file logs -f"
}

handle_stack_start_detached_with_telegram_and_web() {
    # Start the local stack detached including Telegram admin bot listener and nginx web.
    #
    # Args:
    #   $1: compose_file - Path to the Docker Compose file.
    local compose_file="$1"

    echo "🚀 Starting Statechecker stack (detached, with telegram listener + web)..."
    echo ""
    if command -v show_relevant_pages_delayed >/dev/null 2>&1; then
        show_relevant_pages_delayed "$compose_file" 120
    fi
    docker compose --env-file .env -f "$compose_file" --profile telegram --profile web up --build -d
    echo ""
    echo "✅ Services started in background"
    echo "📋 View logs with: docker compose --env-file .env -f $compose_file logs -f"
}

handle_docker_compose_down() {
    # Stop the local stack.
    #
    # Args:
    #   $1: compose_file - Path to the Docker Compose file.
    local compose_file="$1"
    
    echo "🛑 Stopping containers..."
    echo "   Using compose file: $compose_file"
    echo ""
    docker compose --env-file .env -f "$compose_file" down --remove-orphans
    echo ""
    echo "✅ Containers stopped"
}

handle_view_logs() {
    # Tail docker compose logs.
    #
    # Args:
    #   $1: compose_file - Path to the Docker Compose file.
    local compose_file="$1"
    
    echo "📋 Viewing logs..."
    docker compose --env-file .env -f "$compose_file" logs -f
}
