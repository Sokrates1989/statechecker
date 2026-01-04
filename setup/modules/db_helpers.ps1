<#
.SYNOPSIS
    Database initialization and management helpers for Statechecker.

.DESCRIPTION
    This module provides functions used by quick-start.ps1 and menu handlers.

    It supports two initialization modes:
    1) Base schema only (default): install/database/state_checker.sql (no data)
    2) Restore from backup: install/database/backup_*.sql

    Important:
        MySQL initialization scripts run only when the data directory is empty.
        Statechecker uses a local ./db_data directory (bind-mounted into the DB
        container). If ./db_data already contains data, schema/backup switching
        does not take effect unless the directory is moved/reset.
#>

function Get-StatecheckerProjectRoot {
    <#
    .SYNOPSIS
        Get the repository root directory.

    .OUTPUTS
        String: Absolute path to the project root directory.
    #>

    return (Get-Item "$PSScriptRoot\..\..").FullName
}

function Test-DbDataEmpty {
    <#
    .SYNOPSIS
        Check whether ./db_data is missing or empty.

    .PARAMETER ProjectRoot
        Repository root directory.

    .OUTPUTS
        Boolean: True if db_data is missing or empty; False otherwise.
    #>

    param(
        [string]$ProjectRoot = (Get-StatecheckerProjectRoot)
    )

    $dbDataDir = Join-Path $ProjectRoot "db_data"

    if (-not (Test-Path $dbDataDir)) {
        return $true
    }

    $items = Get-ChildItem -Path $dbDataDir -Force -ErrorAction SilentlyContinue
    if (-not $items -or $items.Count -eq 0) {
        return $true
    }

    return $false
}

function Get-AvailableBackups {
    <#
    .SYNOPSIS
        List available backup SQL files (install/database/backup_*.sql).

    .PARAMETER ProjectRoot
        Repository root directory.

    .OUTPUTS
        System.IO.FileInfo[]: Backup files ordered by name descending.
    #>

    param(
        [Parameter(Mandatory = $true)][string]$ProjectRoot
    )

    $backupDir = Join-Path $ProjectRoot "install\database"

    if (-not (Test-Path $backupDir)) {
        return @()
    }

    return Get-ChildItem -Path $backupDir -Filter "backup_*.sql" -File -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending
}

function Invoke-PromptDbInitMode {
    <#
    .SYNOPSIS
        Prompt for DB init mode (schema vs backup).

    .PARAMETER ProjectRoot
        Repository root directory.

    .OUTPUTS
        String: "schema" or full path to selected backup file.
    #>

    param(
        [string]$ProjectRoot = (Get-StatecheckerProjectRoot)
    )

    Write-Host "" 
    Write-Host "Database Initialization" -ForegroundColor Cyan
    Write-Host "=======================" -ForegroundColor Cyan
    Write-Host "" 
    Write-Host "How would you like to initialize the database?"
    Write-Host "1) Base schema only (empty database with tables)"
    Write-Host "2) Restore from backup (includes existing data)"
    Write-Host "" 

    $choice = Read-Host "Your choice (1-2) [1]"
    if ([string]::IsNullOrEmpty($choice)) { $choice = "1" }

    if ($choice -eq "2") {
        $backups = Get-AvailableBackups -ProjectRoot $ProjectRoot
        $backupDir = Join-Path $ProjectRoot "install\database"

        if (-not $backups -or $backups.Count -eq 0) {
            Write-Host "[WARN] No backup files found in $backupDir" -ForegroundColor Yellow
            Write-Host "       Falling back to base schema" -ForegroundColor Yellow
            return "schema"
        }

        Write-Host "" 
        Write-Host "Available backups:"
        $i = 1
        foreach ($backup in $backups) {
            Write-Host "$i) $($backup.Name)"
            $i++
        }
        Write-Host "" 

        $backupChoice = Read-Host "Select backup (1-$($backups.Count)) [1]"
        if ([string]::IsNullOrEmpty($backupChoice)) { $backupChoice = "1" }

        $backupIndex = [int]$backupChoice - 1
        if ($backupIndex -ge 0 -and $backupIndex -lt $backups.Count) {
            Write-Host "[OK] Selected: $($backups[$backupIndex].Name)" -ForegroundColor Green
            return $backups[$backupIndex].FullName
        }

        Write-Host "[WARN] Invalid selection, using base schema" -ForegroundColor Yellow
        return "schema"
    }

    Write-Host "[OK] Using base schema" -ForegroundColor Green
    return "schema"
}

function Enable-SchemaInit {
    <#
    .SYNOPSIS
        Enable schema init line and disable backup line in docker-compose.

    .PARAMETER ComposePath
        Path to docker-compose file.

    .PARAMETER SchemaFilename
        SQL schema filename in install/database.
    #>

    param(
        [Parameter(Mandatory = $true)][string]$ComposePath,
        [string]$SchemaFilename = "state_checker.sql"
    )

    $content = Get-Content $ComposePath -ErrorAction Stop

    for ($i = 0; $i -lt $content.Count; $i++) {
        if ($content[$i] -match "^\s*#\s*- \../install/database/$([regex]::Escape($SchemaFilename)):/docker-entrypoint-initdb\.d/00-schema\.sql:ro") {
            $content[$i] = $content[$i] -replace "^\s*#\s*- ", "      - "
        }

        if ($content[$i] -match "^\s*- \../install/database/$([regex]::Escape($SchemaFilename)):/docker-entrypoint-initdb\.d/00-schema\.sql:ro") {
            # Ensure indentation is consistent.
            $content[$i] = "      - ../install/database/${SchemaFilename}:/docker-entrypoint-initdb.d/00-schema.sql:ro"
        }

        if ($content[$i] -match "^\s*- \../install/database/backup_.*:/docker-entrypoint-initdb\.d/00-backup\.sql:ro") {
            $content[$i] = "      # - ../install/database/backup_CHANGE_ME.sql:/docker-entrypoint-initdb.d/00-backup.sql:ro"
        }

        if ($content[$i] -match "^\s*#\s*- \../install/database/backup_.*:/docker-entrypoint-initdb\.d/00-backup\.sql:ro") {
            $content[$i] = "      # - ../install/database/backup_CHANGE_ME.sql:/docker-entrypoint-initdb.d/00-backup.sql:ro"
        }
    }

    Set-Content -Path $ComposePath -Value $content -Encoding utf8
}

function Enable-BackupInit {
    <#
    .SYNOPSIS
        Enable a specific backup init line and disable schema init line.

    .PARAMETER ComposePath
        Path to docker-compose file.

    .PARAMETER BackupFilename
        Backup SQL filename in install/database.

    .PARAMETER SchemaFilename
        SQL schema filename in install/database.
    #>

    param(
        [Parameter(Mandatory = $true)][string]$ComposePath,
        [Parameter(Mandatory = $true)][string]$BackupFilename,
        [string]$SchemaFilename = "state_checker.sql"
    )

    $content = Get-Content $ComposePath -ErrorAction Stop

    for ($i = 0; $i -lt $content.Count; $i++) {
        if ($content[$i] -match "^\s*- \../install/database/$([regex]::Escape($SchemaFilename)):/docker-entrypoint-initdb\.d/00-schema\.sql:ro") {
            $content[$i] = $content[$i] -replace "^\s*- ", "      # - "
        }

        if ($content[$i] -match "^\s*- \../install/database/backup_.*:/docker-entrypoint-initdb\.d/00-backup\.sql:ro") {
            $content[$i] = "      # - ../install/database/backup_CHANGE_ME.sql:/docker-entrypoint-initdb.d/00-backup.sql:ro"
        }

        if ($content[$i] -match "^\s*#\s*- \../install/database/backup_.*:/docker-entrypoint-initdb\.d/00-backup\.sql:ro") {
            $content[$i] = "      - ../install/database/${BackupFilename}:/docker-entrypoint-initdb.d/00-backup.sql:ro"
        }
    }

    Set-Content -Path $ComposePath -Value $content -Encoding utf8
}

function Set-DbInitSource {
    <#
    .SYNOPSIS
        Apply selected init source (schema or backup) to docker-compose.

    .PARAMETER ComposePath
        Path to docker-compose file.

    .PARAMETER InitSource
        "schema" or full path to selected backup file.

    .PARAMETER SchemaFilename
        SQL schema filename in install/database.
    #>

    param(
        [Parameter(Mandatory = $true)][string]$ComposePath,
        [Parameter(Mandatory = $true)][string]$InitSource,
        [string]$SchemaFilename = "state_checker.sql"
    )

    if ($InitSource -eq "schema" -or $InitSource -eq "keep") {
        Enable-SchemaInit -ComposePath $ComposePath -SchemaFilename $SchemaFilename
        return
    }

    $backupFilename = Split-Path $InitSource -Leaf
    Enable-BackupInit -ComposePath $ComposePath -BackupFilename $backupFilename -SchemaFilename $SchemaFilename
}

function Invoke-DbReinstallInteractive {
    <#
    .SYNOPSIS
        Reinstall the local database by moving db_data and restarting containers.

    .DESCRIPTION
        - Stops docker compose
        - Prompts schema vs backup
        - Updates docker-compose init SQL lines
        - Moves ./db_data to ./db_data__backup_<timestamp> (if non-empty)
        - Starts docker compose

    .PARAMETER ComposeFile
        Compose file path.

    .PARAMETER ProjectName
        Display name used in output.

    .PARAMETER SchemaFilename
        Schema SQL file name.
    #>

    param(
        [Parameter(Mandatory = $true)][string]$ComposeFile,
        [string]$ProjectName = "Statechecker",
        [string]$SchemaFilename = "state_checker.sql"
    )

    $projectRoot = Get-StatecheckerProjectRoot

    if ($ComposeFile -ne "local-deployment\docker-compose.yml" -and $ComposeFile -ne "local-deployment/docker-compose.yml") {
        Write-Host "[WARN] DB re-install is only supported for local-deployment/docker-compose.yml." -ForegroundColor Yellow
        return
    }

    Write-Host "[WARN] This will reset the local db_data directory for $ProjectName." -ForegroundColor Yellow
    Write-Host "       The directory will be MOVED to a backup folder (no auto-delete)." -ForegroundColor Yellow
    Write-Host "" 

    $confirm = Read-Host "Type 'yes' to continue"
    if ($confirm -ne "yes") {
        Write-Host "Cancelled DB re-install." -ForegroundColor Yellow
        return
    }

    $initSource = Invoke-PromptDbInitMode -ProjectRoot $projectRoot
    Set-DbInitSource -ComposePath $ComposeFile -InitSource $initSource -SchemaFilename $SchemaFilename

    Write-Host "" 
    Write-Host "Stopping containers..." -ForegroundColor Yellow
    docker compose --env-file .env -f $ComposeFile down --remove-orphans

    $dbDataDir = Join-Path $projectRoot "db_data"
    if (Test-Path $dbDataDir) {
        $items = Get-ChildItem -Path $dbDataDir -Force -ErrorAction SilentlyContinue
        if ($items -and $items.Count -gt 0) {
            $ts = Get-Date -Format "yyyyMMdd_HHmmss"
            $backupDir = Join-Path $projectRoot ("db_data__backup_{0}" -f $ts)
            Move-Item -Path $dbDataDir -Destination $backupDir -Force
            Write-Host "[OK] Moved db_data -> $(Split-Path $backupDir -Leaf)" -ForegroundColor Green
        }
    }

    if (-not (Test-Path $dbDataDir)) {
        New-Item -ItemType Directory -Path $dbDataDir -Force | Out-Null
    }

    Write-Host "" 
    Write-Host "Starting stack..." -ForegroundColor Cyan
    docker compose --env-file .env -f $ComposeFile up --build
}
