#!/bin/bash
#
# db_helpers.sh
#
# Database initialization and management module for Statechecker.
#
# This module provides helper functions used by quick-start.sh and menu_handlers.sh
# to initialize the database either from a clean schema (default) or from a backup
# file (backup_*.sql).
#

# Get the project root directory.
# Outputs:
#   Absolute path to the project root directory.
_get_project_root() {
    local script_path="${BASH_SOURCE[0]}"
    local script_dir
    script_dir="$(cd "$(dirname "$script_path")" && pwd)"

    local git_root
    git_root=$(git -C "$script_dir" rev-parse --show-toplevel 2>/dev/null || true)
    if [ -n "$git_root" ]; then
        echo "$git_root"
        return
    fi

    local current="$script_dir"
    while [ -n "$current" ] && [ "$current" != "/" ]; do
        if [ -d "$current/install/database" ]; then
            echo "$current"
            return
        fi
        current="$(dirname "$current")"
    done

    echo "$(cd "$script_dir/../.." && pwd)"
}

# Portable sed -i wrapper for macOS vs Linux/Git-Bash.
# Args:
#   $1: file path
#   $2..: sed arguments
_sed_inplace() {
    local file="$1"
    shift

    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "$@" "$file"
    else
        sed -i "$@" "$file"
    fi
}

# Prompt for database initialization mode (base schema or backup).
# Args:
#   $1: project root directory
# Returns:
#   "schema" or full path to selected backup file.
prompt_db_init_mode() {
    local project_root="${1:-$(_get_project_root)}"

    local backup_dir="${project_root}/install/database"

    echo "" >&2
    echo "🗄️  Database Initialization" >&2
    echo "===========================" >&2
    echo "" >&2
    echo "How would you like to initialize the database?" >&2
    echo "1) Base schema only (empty database with tables)" >&2
    echo "2) Restore from backup (includes existing data)" >&2
    echo "" >&2

    local db_init_choice
    read -r -p "Your choice (1-2) [1]: " db_init_choice
    db_init_choice="${db_init_choice:-1}"

    if [ "$db_init_choice" = "2" ]; then
        local backups
        mapfile -t backups < <(find "$backup_dir" -maxdepth 1 -name "backup_*.sql" -type f 2>/dev/null | sort -r)

        if [ ${#backups[@]} -eq 0 ]; then
            echo "⚠️  No backup files found in $backup_dir" >&2
            echo "   Falling back to base schema" >&2
            echo "schema"
            return
        fi

        echo "" >&2
        echo "Available backups:" >&2
        local i=1
        for backup in "${backups[@]}"; do
            echo "$i) $(basename "$backup")" >&2
            ((i++))
        done
        echo "" >&2

        local backup_choice
        read -r -p "Select backup (1-${#backups[@]}) [1]: " backup_choice
        backup_choice="${backup_choice:-1}"

        if [[ "$backup_choice" =~ ^[0-9]+$ ]] && [ "$backup_choice" -ge 1 ] && [ "$backup_choice" -le ${#backups[@]} ]; then
            local selected_backup="${backups[$((backup_choice-1))]}"
            echo "✅ Selected: $(basename "$selected_backup")" >&2
            echo "$selected_backup"
        else
            echo "⚠️  Invalid selection, using base schema" >&2
            echo "schema"
        fi
    else
        echo "✅ Using base schema" >&2
        echo "schema"
    fi
}

# Update docker-compose.yml to use the selected init source.
# Args:
#   $1: compose_path
#   $2: init_source ("schema" or full path to backup file)
#   $3: schema_filename (default: state_checker.sql)
apply_db_init_source() {
    local compose_path="$1"
    local init_source="$2"
    local schema_filename="${3:-state_checker.sql}"

    if [ "$init_source" = "schema" ] || [ "$init_source" = "keep" ]; then
        _enable_schema_init "$compose_path" "$schema_filename"
    else
        local backup_filename
        backup_filename="$(basename "$init_source")"
        _enable_backup_init "$compose_path" "$backup_filename" "$schema_filename"
    fi
}

# Internal: Enable schema-based initialization.
_enable_schema_init() {
    local compose_path="$1"
    local schema_filename="${2:-state_checker.sql}"

    _sed_inplace "$compose_path" "s|^      # - ../install/database/${schema_filename}:/docker-entrypoint-initdb.d/00-schema.sql:ro|      - ../install/database/${schema_filename}:/docker-entrypoint-initdb.d/00-schema.sql:ro|" \
        2>/dev/null || true

    _sed_inplace "$compose_path" "s|^      - ../install/database/backup_.*:/docker-entrypoint-initdb.d/00-backup.sql:ro|      # - ../install/database/backup_CHANGE_ME.sql:/docker-entrypoint-initdb.d/00-backup.sql:ro|" \
        2>/dev/null || true
}

# Internal: Enable backup-based initialization.
_enable_backup_init() {
    local compose_path="$1"
    local backup_filename="$2"
    local schema_filename="${3:-state_checker.sql}"

    _sed_inplace "$compose_path" "s|^      - ../install/database/${schema_filename}:/docker-entrypoint-initdb.d/00-schema.sql:ro|      # - ../install/database/${schema_filename}:/docker-entrypoint-initdb.d/00-schema.sql:ro|" \
        2>/dev/null || true

    # Ensure the backup init line exists and points to the selected backup.
    # 1) If a backup line is already active, update it to the selected backup.
    _sed_inplace "$compose_path" "s|^      - ../install/database/backup_.*:/docker-entrypoint-initdb.d/00-backup.sql:ro|      - ../install/database/${backup_filename}:/docker-entrypoint-initdb.d/00-backup.sql:ro|" \
        2>/dev/null || true

    # 2) If the backup line is commented, uncomment it and set the selected backup.
    _sed_inplace "$compose_path" "s|^      # - ../install/database/backup_.*:/docker-entrypoint-initdb.d/00-backup.sql:ro|      - ../install/database/${backup_filename}:/docker-entrypoint-initdb.d/00-backup.sql:ro|" \
        2>/dev/null || true
}

# Check if db_data directory is empty.
# Returns:
#   0 if empty (or missing), 1 if non-empty.
is_db_data_empty() {
    local project_root
    project_root="$(_get_project_root)"

    local db_data_dir="${project_root}/db_data"
    if [ ! -d "$db_data_dir" ]; then
        return 0
    fi

    if [ -z "$(ls -A "$db_data_dir" 2>/dev/null)" ]; then
        return 0
    fi

    return 1
}

# Handle DB reinstall from menu.
# This will stop the stack, move db_data to a timestamped backup folder, then restart.
# Args:
#   $1: compose_file
#   $2: project_name
#   $3: schema_filename
handle_db_reinstall_interactive() {
    local compose_file="$1"
    local project_name="${2:-Project}"
    local schema_filename="${3:-state_checker.sql}"

    local project_root
    project_root="$(_get_project_root)"

    if [ "$compose_file" != "local-deployment/docker-compose.yml" ]; then
        echo "⚠️  DB re-install is only supported for local-deployment/docker-compose.yml." >&2
        return 1
    fi

    echo "⚠️  This will reset the local database directory (db_data) for ${project_name}."
    echo "    Your current db_data will be MOVED to a backup folder (no auto-delete)."
    echo "" 
    echo "If you want to preserve your current data as SQL, create a backup first (e.g. via phpMyAdmin)."
    echo "Local phpMyAdmin (if enabled) is available at http://localhost:\${PHPMYADMIN_PORT:-8080}"
    echo ""

    local confirm
    read -r -p "Type 'yes' to continue: " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Cancelled DB re-install."
        return 1
    fi

    local init_source
    init_source=$(prompt_db_init_mode "$project_root")
    apply_db_init_source "$compose_file" "$init_source" "$schema_filename"

    echo "" 
    echo "🛑 Stopping stack..."
    docker compose --env-file .env -f "$compose_file" down --remove-orphans

    local db_data_dir="${project_root}/db_data"
    if [ -d "$db_data_dir" ] && [ -n "$(ls -A "$db_data_dir" 2>/dev/null)" ]; then
        local ts
        ts="$(date +%Y%m%d_%H%M%S)"
        local backup_dir="${project_root}/db_data__backup_${ts}"
        echo "📦 Moving existing db_data -> $(basename "$backup_dir")"
        mv "$db_data_dir" "$backup_dir"
    fi

    mkdir -p "$db_data_dir"

    echo "" 
    echo "🚀 Starting stack..."
    docker compose --env-file .env -f "$compose_file" up --build
}
