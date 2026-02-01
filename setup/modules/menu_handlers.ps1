<#
.SYNOPSIS
    Menu display module for Statechecker quick-start script.

.DESCRIPTION
    This module provides the main menu display and routing logic for the
    Statechecker quick-start script. Action handlers are delegated to
    specialized modules (menu_stack, menu_build, menu_keycloak, db_helpers).

.NOTES
    Author: Auto-generated
    Date: 2026-01-29
    Version: 2.0.0

.DEPENDENCIES
    - menu_stack.ps1: Stack start/stop operations
    - menu_build.ps1: Docker image build operations
    - menu_keycloak.ps1: Keycloak bootstrap operations
    - db_helpers.ps1: Database reinstall operations
#>

$scriptPath = $PSScriptRoot

# Source dependencies
$dbHelpersPath = Join-Path $scriptPath "db_helpers.ps1"
if (Test-Path $dbHelpersPath) {
    . $dbHelpersPath
}

$menuStackPath = Join-Path $scriptPath "menu_stack.ps1"
if (Test-Path $menuStackPath) {
    . $menuStackPath
}

$menuBuildPath = Join-Path $scriptPath "menu_build.ps1"
if (Test-Path $menuBuildPath) {
    . $menuBuildPath
}

$menuKeycloakPath = Join-Path $scriptPath "menu_keycloak.ps1"
if (Test-Path $menuKeycloakPath) {
    . $menuKeycloakPath
}

function Invoke-DbReinstall {
    <#
    .SYNOPSIS
        Reinstall the database by moving db_data aside and reinitializing schema/backup.

    .PARAMETER ComposeFile
        Path to the Docker Compose file.
    #>
    param([string]$ComposeFile)
    Invoke-DbReinstallInteractive -ComposeFile $ComposeFile -ProjectName "Statechecker" -SchemaFilename "state_checker.sql"
}

function Show-MainMenu {
    <#
    .SYNOPSIS
        Show the interactive quick-start menu.

    .PARAMETER ComposeFile
        Path to the Docker Compose file.
    #>
    param([string]$ComposeFile)

    $summary = $null
    $exitCode = 0

    # Menu item numbering
    $menuNext = 1
    $MENU_RUN_START = $menuNext; $menuNext++
    $MENU_RUN_START_DETACHED = $menuNext; $menuNext++

    $MENU_MONITOR_LOGS = $menuNext; $menuNext++

    $MENU_MAINT_DOWN = $menuNext; $menuNext++
    $MENU_MAINT_DB_REINSTALL = $menuNext; $menuNext++

    $MENU_BUILD_IMAGE = $menuNext; $menuNext++
    $MENU_BUILD_WEB_IMAGE = $menuNext; $menuNext++

    $MENU_KEYCLOAK_BOOTSTRAP = $menuNext; $menuNext++

    $MENU_EXIT = $menuNext

    Write-Host "" 
    Write-Host "================ Main Menu ================" -ForegroundColor Yellow
    Write-Host "" 
    Write-Host "Run:" -ForegroundColor Yellow
    Write-Host "  $MENU_RUN_START) Start all services" -ForegroundColor Gray
    Write-Host "  $MENU_RUN_START_DETACHED) Start all services (detached)" -ForegroundColor Gray
    Write-Host "" 
    Write-Host "Monitoring:" -ForegroundColor Yellow
    Write-Host "  $MENU_MONITOR_LOGS) View logs" -ForegroundColor Gray
    Write-Host "" 
    Write-Host "Maintenance:" -ForegroundColor Yellow
    Write-Host "  $MENU_MAINT_DOWN) Docker Compose Down (stop containers)" -ForegroundColor Gray
    Write-Host "  $MENU_MAINT_DB_REINSTALL) DB Re-Install (reset database volume)" -ForegroundColor Gray
    Write-Host "" 
    Write-Host "Build:" -ForegroundColor Yellow
    Write-Host "  $MENU_BUILD_IMAGE) Build Production Docker Image" -ForegroundColor Gray
    Write-Host "  $MENU_BUILD_WEB_IMAGE) Build Website Docker Image (nginx)" -ForegroundColor Gray
    Write-Host "" 
    Write-Host "Keycloak:" -ForegroundColor Yellow
    Write-Host "  $MENU_KEYCLOAK_BOOTSTRAP) Bootstrap Keycloak (realm/clients/users)" -ForegroundColor Gray
    Write-Host "" 
    Write-Host "  $MENU_EXIT) Exit" -ForegroundColor Gray
    Write-Host "" 
    $choice = Read-Host "Your choice (1-$MENU_EXIT)"

    switch ($choice) {
        "$MENU_RUN_START" {
            Start-StackWithTelegramAndWeb -ComposeFile $ComposeFile -LogToFile
            $summary = "All services started"
        }
        "$MENU_RUN_START_DETACHED" {
            Start-StackDetachedWithTelegramAndWeb -ComposeFile $ComposeFile
            $summary = "All services started in background"
        }
        "$MENU_MONITOR_LOGS" {
            Show-Logs -ComposeFile $ComposeFile
            $summary = "Logs viewed"
        }
        "$MENU_MAINT_DOWN" {
            Invoke-DockerComposeDown -ComposeFile $ComposeFile
            $summary = "Docker Compose Down executed"
        }
        "$MENU_BUILD_IMAGE" {
            Build-ProductionImage
            $summary = "Image build executed"
        }
        "$MENU_BUILD_WEB_IMAGE" {
            Build-WebsiteImage
            $summary = "Website image build executed"
        }
        "$MENU_MAINT_DB_REINSTALL" {
            Invoke-DbReinstall -ComposeFile $ComposeFile
            $summary = "DB re-install executed"
        }
        "$MENU_KEYCLOAK_BOOTSTRAP" {
            Invoke-KeycloakBootstrap
            $summary = "Keycloak bootstrap executed"
        }
        "$MENU_EXIT" {
            Write-Host "Goodbye!" -ForegroundColor Cyan
            exit 0
        }
        Default {
            Write-Host "[ERROR] Invalid selection. Please re-run the script." -ForegroundColor Yellow
            exit 1
        }
    }

    Write-Host ""
    if ($summary) {
        Write-Host "[OK] $summary" -ForegroundColor Green
    }
    Write-Host "[INFO] Quick-start finished. Run again for more actions." -ForegroundColor Cyan
    Write-Host ""
    exit $exitCode
}
