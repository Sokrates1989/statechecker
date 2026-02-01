#!/bin/bash
#
# menu_handlers.sh
#
# Menu display module for Statechecker quick-start script.
# This module provides the main menu display and routing logic.
# Action handlers are delegated to specialized modules.
#
# Author: Auto-generated
# Date: 2026-01-29
# Version: 2.0.0
#
# Dependencies:
#   - menu_stack.sh: Stack start/stop operations
#   - menu_build.sh: Docker image build operations
#   - menu_keycloak.sh: Keycloak bootstrap operations
#   - db_helpers.sh: Database reinstall operations

MENU_HANDLERS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source dependencies
if [ -f "${MENU_HANDLERS_DIR}/db_helpers.sh" ]; then
    source "${MENU_HANDLERS_DIR}/db_helpers.sh"
fi

if [ -f "${MENU_HANDLERS_DIR}/menu_stack.sh" ]; then
    source "${MENU_HANDLERS_DIR}/menu_stack.sh"
fi

if [ -f "${MENU_HANDLERS_DIR}/menu_build.sh" ]; then
    source "${MENU_HANDLERS_DIR}/menu_build.sh"
fi

if [ -f "${MENU_HANDLERS_DIR}/menu_keycloak.sh" ]; then
    source "${MENU_HANDLERS_DIR}/menu_keycloak.sh"
fi

read_prompt() {
    # Read a prompt from stdin (works in interactive and non-interactive shells).
    #
    # Args:
    #   $1: prompt text
    #   $2: variable name
    local prompt="$1"
    local var_name="$2"

    if [[ -r /dev/tty ]]; then
        read -r -p "$prompt" "$var_name" < /dev/tty
    else
        read -r -p "$prompt" "$var_name"
    fi
}

handle_db_reinstall() {
    # Reinstall the DB by moving db_data to a backup folder and re-initializing.
    #
    # Args:
    #   $1: compose_file - Path to the Docker Compose file.
    local compose_file="$1"
    handle_db_reinstall_interactive "$compose_file" "Statechecker" "state_checker.sql"
}

show_main_menu() {
    # Show the interactive quick-start menu.
    #
    # Args:
    #   $1: compose_file - Path to the Docker Compose file.
    local compose_file="$1"
    
    local summary_msg=""
    local exit_code=0
    local choice

    while true; do
        local MENU_NEXT=1
        local MENU_RUN_START=$MENU_NEXT; MENU_NEXT=$((MENU_NEXT+1))
        local MENU_RUN_START_DETACHED=$MENU_NEXT; MENU_NEXT=$((MENU_NEXT+1))

        local MENU_MONITOR_LOGS=$MENU_NEXT; MENU_NEXT=$((MENU_NEXT+1))

        local MENU_MAINT_DOWN=$MENU_NEXT; MENU_NEXT=$((MENU_NEXT+1))
        local MENU_MAINT_DB_REINSTALL=$MENU_NEXT; MENU_NEXT=$((MENU_NEXT+1))

        local MENU_BUILD_IMAGE=$MENU_NEXT; MENU_NEXT=$((MENU_NEXT+1))
        local MENU_BUILD_WEB_IMAGE=$MENU_NEXT; MENU_NEXT=$((MENU_NEXT+1))

        local MENU_KEYCLOAK_BOOTSTRAP=$MENU_NEXT; MENU_NEXT=$((MENU_NEXT+1))

        local MENU_EXIT=$MENU_NEXT

        echo ""
        echo "================ Main Menu ================"
        echo ""
        echo "Run:"
        echo "  ${MENU_RUN_START}) Start all services"
        echo "  ${MENU_RUN_START_DETACHED}) Start all services (detached)"
        echo ""
        echo "Monitoring:"
        echo "  ${MENU_MONITOR_LOGS}) View logs"
        echo ""
        echo "Maintenance:"
        echo "  ${MENU_MAINT_DOWN}) Docker Compose Down (stop containers)"
        echo "  ${MENU_MAINT_DB_REINSTALL}) DB Re-Install (reset database volume)"
        echo ""
        echo "Build:"
        echo "  ${MENU_BUILD_IMAGE}) Build Production Docker Image"
        echo "  ${MENU_BUILD_WEB_IMAGE}) Build Website Docker Image (nginx)"
        echo ""
        echo "Keycloak:"
        echo "  ${MENU_KEYCLOAK_BOOTSTRAP}) Bootstrap Keycloak (realm/clients/users)"
        echo ""
        echo "  ${MENU_EXIT}) Exit"
        echo ""

        read_prompt "Your choice (1-${MENU_EXIT}): " choice

        case $choice in
          ${MENU_RUN_START})
            handle_stack_start_with_telegram_and_web "$compose_file" "true"
            summary_msg="All services started"
            break
            ;;
          ${MENU_RUN_START_DETACHED})
            handle_stack_start_detached_with_telegram_and_web "$compose_file"
            summary_msg="All services started in background"
            break
            ;;
          ${MENU_MONITOR_LOGS})
            handle_view_logs "$compose_file"
            summary_msg="Logs viewed"
            break
            ;;
          ${MENU_MAINT_DOWN})
            handle_docker_compose_down "$compose_file"
            summary_msg="Docker Compose Down executed"
            break
            ;;
          ${MENU_BUILD_IMAGE})
            handle_build_image
            summary_msg="Image build executed"
            break
            ;;
          ${MENU_BUILD_WEB_IMAGE})
            handle_build_web_image
            summary_msg="Website image build executed"
            break
            ;;
          ${MENU_MAINT_DB_REINSTALL})
            handle_db_reinstall "$compose_file"
            summary_msg="DB re-install executed"
            break
            ;;
          ${MENU_KEYCLOAK_BOOTSTRAP})
            handle_keycloak_bootstrap
            summary_msg="Keycloak bootstrap executed"
            break
            ;;
          ${MENU_EXIT})
            echo "👋 Goodbye!"
            exit 0
            ;;
          *)
            echo "❌ Invalid selection. Please try again."
            echo ""
            continue
            ;;
        esac
    done

    echo ""
    if [ -n "$summary_msg" ]; then
        echo "✅ $summary_msg"
    fi
    echo "ℹ️  Quick-start finished. Run again for more actions."
    echo ""
    exit $exit_code
}
