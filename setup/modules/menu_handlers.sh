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
        echo "Choose an option:"
        echo "1) Start stack (docker compose up)"
        echo "2) Start stack detached (background)"
        echo "3) View logs"
        echo "4) Docker Compose Down (stop containers)"
        echo "5) Build Production Docker Image"
        echo "6) DB Re-Install (reset database volume)"
        echo "7) Exit"
        echo ""

        read -p "Your choice (1-7): " choice

        case $choice in
          1)
            handle_stack_start "$compose_file"
            summary_msg="Stack started"
            break
            ;;
          2)
            handle_stack_start_detached "$compose_file"
            summary_msg="Stack started in background"
            break
            ;;
          3)
            handle_view_logs "$compose_file"
            summary_msg="Logs viewed"
            break
            ;;
          4)
            handle_docker_compose_down "$compose_file"
            summary_msg="Docker Compose Down executed"
            break
            ;;
          5)
            handle_build_image
            summary_msg="Image build executed"
            break
            ;;
          6)
            handle_db_reinstall "$compose_file"
            summary_msg="DB re-install executed"
            break
            ;;
          7)
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
