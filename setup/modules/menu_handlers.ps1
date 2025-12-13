# menu_handlers.ps1
# PowerShell module for handling menu actions

function Start-Stack {
    param([string]$ComposeFile)
    
    Write-Host "[START] Starting Statechecker stack..." -ForegroundColor Cyan
    Write-Host ""
    docker compose --env-file .env -f $ComposeFile up --build
}

function Start-StackDetached {
    param([string]$ComposeFile)
    
    Write-Host "[START] Starting Statechecker stack (detached)..." -ForegroundColor Cyan
    Write-Host ""
    docker compose --env-file .env -f $ComposeFile up --build -d
    Write-Host ""
    Write-Host "[OK] Services started in background" -ForegroundColor Green
    Write-Host "View logs with: docker compose --env-file .env -f $ComposeFile logs -f" -ForegroundColor Gray
}

function Invoke-DockerComposeDown {
    param([string]$ComposeFile)
    
    Write-Host "[STOP] Stopping containers..." -ForegroundColor Yellow
    Write-Host "   Using compose file: $ComposeFile" -ForegroundColor Gray
    Write-Host ""
    docker compose --env-file .env -f $ComposeFile down
    Write-Host ""
    Write-Host "[OK] Containers stopped" -ForegroundColor Green
}

function Build-ProductionImage {
    Write-Host "[BUILD] Building production Docker image..." -ForegroundColor Cyan
    Write-Host ""
    if (Test-Path "build-image\build-image.ps1") {
        & .\build-image\build-image.ps1
    } elseif (Test-Path "build-image\build-image.sh") {
        Write-Host "Running build-image.sh via bash..." -ForegroundColor Yellow
        bash build-image/build-image.sh
    } else {
        Write-Host "[ERROR] build-image script not found" -ForegroundColor Red
    }
}

function Show-Logs {
    param([string]$ComposeFile)
    
    Write-Host "[LOGS] Viewing logs..." -ForegroundColor Cyan
    docker compose --env-file .env -f $ComposeFile logs -f
}

function Invoke-DbReinstall {
    param([string]$ComposeFile)

    if ($ComposeFile -ne 'local-deployment\docker-compose.yml') {
        Write-Host "[WARN] DB re-install is only supported for local-deployment/docker-compose.yml." -ForegroundColor Yellow
        return
    }

    Write-Host "[WARN] This will completely reset the database volume (db_data) for Statechecker." -ForegroundColor Yellow
    Write-Host "       All existing data in that volume will be LOST." -ForegroundColor Yellow
    Write-Host "" 
    Write-Host "If you want to preserve your current data, create a backup first (e.g. via phpMyAdmin)." -ForegroundColor Yellow
    Write-Host "Local phpMyAdmin (if enabled) is available at http://localhost:`$(`$env:PHPMYADMIN_PORT ?? '8080')" -ForegroundColor Yellow
    Write-Host "" 
    $confirm = Read-Host "Type 'yes' to continue"
    if ($confirm -ne 'yes') {
        Write-Host "Cancelled DB re-install." -ForegroundColor Yellow
        return
    }

    Write-Host "" 
    Write-Host "Recreating containers and database volume (docker compose down -v / up --build)..." -ForegroundColor Cyan
    docker compose --env-file .env -f $ComposeFile down -v
    docker compose --env-file .env -f $ComposeFile up --build
}

function Show-MainMenu {
    param([string]$ComposeFile)

    $summary = $null
    $exitCode = 0

    $menuNext = 1
    $MENU_RUN_START = $menuNext; $menuNext++
    $MENU_RUN_START_DETACHED = $menuNext; $menuNext++

    $MENU_MONITOR_LOGS = $menuNext; $menuNext++

    $MENU_MAINT_DOWN = $menuNext; $menuNext++
    $MENU_MAINT_DB_REINSTALL = $menuNext; $menuNext++

    $MENU_BUILD_IMAGE = $menuNext; $menuNext++

    $MENU_EXIT = $menuNext

    Write-Host "" 
    Write-Host "================ Main Menu ================" -ForegroundColor Yellow
    Write-Host "" 
    Write-Host "Run:" -ForegroundColor Yellow
    Write-Host "  $MENU_RUN_START) Start stack (docker compose up)" -ForegroundColor Gray
    Write-Host "  $MENU_RUN_START_DETACHED) Start stack detached (background)" -ForegroundColor Gray
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
    Write-Host "" 
    Write-Host "  $MENU_EXIT) Exit" -ForegroundColor Gray
    Write-Host "" 
    $choice = Read-Host "Your choice (1-$MENU_EXIT)"

    switch ($choice) {
        "$MENU_RUN_START" {
            Start-Stack -ComposeFile $ComposeFile
            $summary = "Stack started"
        }
        "$MENU_RUN_START_DETACHED" {
            Start-StackDetached -ComposeFile $ComposeFile
            $summary = "Stack started in background"
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
        "$MENU_MAINT_DB_REINSTALL" {
            Invoke-DbReinstall -ComposeFile $ComposeFile
            $summary = "DB re-install executed"
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
