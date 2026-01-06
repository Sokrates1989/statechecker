#!/bin/bash
#
# menu_handlers.sh
#
# Module for handling menu actions in quick-start script

 MENU_HANDLERS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
 if [ -f "${MENU_HANDLERS_DIR}/db_helpers.sh" ]; then
     source "${MENU_HANDLERS_DIR}/db_helpers.sh"
 fi

read_prompt() {
    # Read a prompt from stdin (works in interactive and non-interactive shells).
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

handle_build_web_image() {
    echo "🏗️  Building website Docker image (nginx)..."
    echo ""

    if [ ! -f "Dockerfile_web" ]; then
        echo "❌ Dockerfile_web not found"
        return 1
    fi

    local image_name="sokrates1989/statechecker-web"
    local image_version="latest"

    if [ -f .env ]; then
        image_name=$(grep "^WEB_IMAGE_NAME=" .env 2>/dev/null | cut -d'=' -f2- | tr -d ' "' || echo "$image_name")
        image_version=$(grep "^WEB_IMAGE_VERSION=" .env 2>/dev/null | cut -d'=' -f2- | tr -d ' "' || echo "$image_version")
    fi

    read_prompt "Website image name [$image_name]: " input_name
    if [ -n "$input_name" ]; then
        image_name="$input_name"
    fi

    read_prompt "Website image version [$image_version]: " input_version
    if [ -n "$input_version" ]; then
        image_version="$input_version"
    fi
    if [ -z "$image_version" ]; then
        image_version="latest"
    fi

    local full_image="${image_name}:${image_version}"
    local target_platform="${TARGET_PLATFORM:-linux/amd64}"

    echo "" 
    echo "📦 Building: $full_image"
    echo "Target platform: $target_platform"

    if docker buildx version >/dev/null 2>&1; then
        docker buildx build --platform "$target_platform" -t "$full_image" -f Dockerfile_web --build-arg "WEB_IMAGE_TAG=$image_version" --load .
    else
        docker build -t "$full_image" -f Dockerfile_web --build-arg "WEB_IMAGE_TAG=$image_version" .
    fi

    echo "📤 Pushing image to registry..."
    docker push "$full_image"
    echo "✅ Image pushed: $full_image"

    if [ "$image_version" != "latest" ]; then
        echo ""
        echo "📤 Tagging and pushing ${image_name}:latest..."
        docker tag "$full_image" "${image_name}:latest"
        docker push "${image_name}:latest"
        echo "✅ Also pushed: ${image_name}:latest"
    fi

    if [ -f .env ]; then
        if grep -q '^WEB_IMAGE_NAME=' .env; then
            tmp_env="$(mktemp)" || return 1
            sed "s|^WEB_IMAGE_NAME=.*|WEB_IMAGE_NAME=$image_name|" .env > "$tmp_env" && mv "$tmp_env" .env
        else
            echo "WEB_IMAGE_NAME=$image_name" >> .env
        fi
        if grep -q '^WEB_IMAGE_VERSION=' .env; then
            tmp_env="$(mktemp)" || return 1
            sed "s|^WEB_IMAGE_VERSION=.*|WEB_IMAGE_VERSION=$image_version|" .env > "$tmp_env" && mv "$tmp_env" .env
        else
            echo "WEB_IMAGE_VERSION=$image_version" >> .env
        fi
    fi
}

handle_stack_start_detached_with_telegram() {
    # Start the local stack detached including the Telegram admin bot listener.
    # Args:
    #   $1: compose_file
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
    # Args:
    #   $1: compose_file
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

handle_db_reinstall() {
    # Reinstall the DB by moving db_data to a backup folder and re-initializing.
    # Args:
    #   $1: compose_file
    local compose_file="$1"
    handle_db_reinstall_interactive "$compose_file" "Statechecker" "state_checker.sql"
}

handle_stack_start() {
    # Start the local stack in foreground.
    # Args:
    #   $1: compose_file
    local compose_file="$1"
    
    echo "🚀 Starting Statechecker stack..."
    echo ""
    if command -v show_relevant_pages_delayed >/dev/null 2>&1; then
        show_relevant_pages_delayed "$compose_file" 120
    fi
    docker compose --env-file .env -f "$compose_file" up --build
}

handle_stack_start_with_telegram() {
    # Start the local stack in foreground including the Telegram admin bot listener.
    # Args:
    #   $1: compose_file
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
    # Args:
    #   $1: compose_file
    local compose_file="$1"

    echo "🚀 Starting Statechecker stack (with telegram listener + web)..."
    echo ""
    if command -v show_relevant_pages_delayed >/dev/null 2>&1; then
        show_relevant_pages_delayed "$compose_file" 120
    fi
    docker compose --env-file .env -f "$compose_file" --profile telegram --profile web up --build
}

handle_stack_start_detached() {
    # Start the local stack detached.
    # Args:
    #   $1: compose_file
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

handle_docker_compose_down() {
    # Stop the local stack.
    # Args:
    #   $1: compose_file
    local compose_file="$1"
    
    echo "🛑 Stopping containers..."
    echo "   Using compose file: $compose_file"
    echo ""
    docker compose --env-file .env -f "$compose_file" down --remove-orphans
    echo ""
    echo "✅ Containers stopped"
}

handle_build_image() {
    # Build the production image (if build-image script exists).
    echo "🏗️  Building production Docker image..."
    echo ""
    if [ -f "build-image/build-image.sh" ]; then
        bash build-image/build-image.sh
    else
        echo "❌ build-image/build-image.sh not found"
    fi
}

handle_view_logs() {
    # Tail docker compose logs.
    # Args:
    #   $1: compose_file
    local compose_file="$1"
    
    echo "📋 Viewing logs..."
    docker compose --env-file .env -f "$compose_file" logs -f
}

show_main_menu() {
    # Show the interactive quick-start menu.
    # Args:
    #   $1: compose_file
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
        echo "  ${MENU_EXIT}) Exit"
        echo ""

        read_prompt "Your choice (1-${MENU_EXIT}): " choice

        case $choice in
          ${MENU_RUN_START})
            handle_stack_start_with_telegram_and_web "$compose_file"
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
