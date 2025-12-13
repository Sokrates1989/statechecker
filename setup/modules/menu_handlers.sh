#!/bin/bash
#
# menu_handlers.sh
#
# Module for handling menu actions in quick-start script

handle_db_reinstall() {
    local compose_file="$1"

    if [ "$compose_file" != "local-deployment/docker-compose.yml" ]; then
        echo "⚠️  DB re-install is only supported for local-deployment/docker-compose.yml."
        return
    fi

    echo "⚠️  This will completely reset the database volume (db_data) for Statechecker."
    echo "    All existing data in that volume will be LOST."
    echo ""
    echo "If you want to preserve your current data, create a backup first (e.g. via phpMyAdmin)."
    echo "Local phpMyAdmin (if enabled) is available at http://localhost:\${PHPMYADMIN_PORT:-8080}"
    echo ""
    read -p "Type 'yes' to continue: " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Cancelled DB re-install."
        return
    fi

    echo ""
    echo "🧹 Recreating containers and database volume (docker compose down -v / up --build)..."
    docker compose --env-file .env -f "$compose_file" down -v
    docker compose --env-file .env -f "$compose_file" up --build
}

handle_stack_start() {
    local compose_file="$1"
    
    echo "🚀 Starting Statechecker stack..."
    echo ""
    docker compose --env-file .env -f "$compose_file" up --build
}

handle_stack_start_detached() {
    local compose_file="$1"
    
    echo "🚀 Starting Statechecker stack (detached)..."
    echo ""
    docker compose --env-file .env -f "$compose_file" up --build -d
    echo ""
    echo "✅ Services started in background"
    echo "📋 View logs with: docker compose --env-file .env -f $compose_file logs -f"
}

handle_docker_compose_down() {
    local compose_file="$1"
    
    echo "🛑 Stopping containers..."
    echo "   Using compose file: $compose_file"
    echo ""
    docker compose --env-file .env -f "$compose_file" down
    echo ""
    echo "✅ Containers stopped"
}

handle_build_image() {
    echo "🏗️  Building production Docker image..."
    echo ""
    if [ -f "build-image/build-image.sh" ]; then
        bash build-image/build-image.sh
    else
        echo "❌ build-image/build-image.sh not found"
    fi
}

handle_view_logs() {
    local compose_file="$1"
    
    echo "📋 Viewing logs..."
    docker compose --env-file .env -f "$compose_file" logs -f
}

show_main_menu() {
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

        local MENU_EXIT=$MENU_NEXT

        echo ""
        echo "================ Main Menu ================"
        echo ""
        echo "Run:"
        echo "  ${MENU_RUN_START}) Start stack (docker compose up)"
        echo "  ${MENU_RUN_START_DETACHED}) Start stack detached (background)"
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
        echo ""
        echo "  ${MENU_EXIT}) Exit"
        echo ""

        read -p "Your choice (1-${MENU_EXIT}): " choice

        case $choice in
          ${MENU_RUN_START})
            handle_stack_start "$compose_file"
            summary_msg="Stack started"
            break
            ;;
          ${MENU_RUN_START_DETACHED})
            handle_stack_start_detached "$compose_file"
            summary_msg="Stack started in background"
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
          ${MENU_MAINT_DB_REINSTALL})
            handle_db_reinstall "$compose_file"
            summary_msg="DB re-install executed"
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
