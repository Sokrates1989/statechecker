# menu_handlers.ps1
# PowerShell module for handling menu actions

 $scriptPath = $PSScriptRoot
 $dbHelpersPath = Join-Path $scriptPath "db_helpers.ps1"
 if (Test-Path $dbHelpersPath) {
     . $dbHelpersPath
 }

function Build-WebsiteImage {
    <#
    .SYNOPSIS
        Build the nginx-based admin website Docker image (Dockerfile_web).
    #>

    Write-Host "[BUILD] Building website Docker image (nginx)..." -ForegroundColor Cyan
    Write-Host ""

    if (-not (Test-Path "Dockerfile_web")) {
        Write-Host "[ERROR] Dockerfile_web not found" -ForegroundColor Red
        return
    }

    $IMAGE_NAME = "sokrates1989/statechecker-web"
    $IMAGE_VERSION = "latest"

    if (Test-Path .env) {
        $envContent = Get-Content .env -ErrorAction SilentlyContinue

        $nameLine = $envContent | Where-Object { $_ -match "^WEB_IMAGE_NAME=" }
        if ($nameLine) {
            $IMAGE_NAME = ($nameLine -split "=", 2)[1].Trim().Trim('"')
        }

        $versionLine = $envContent | Where-Object { $_ -match "^WEB_IMAGE_VERSION=" }
        if ($versionLine) {
            $IMAGE_VERSION = ($versionLine -split "=", 2)[1].Trim().Trim('"')
        }
    }

    $inputName = Read-Host "Website image name [$IMAGE_NAME]"
    if (-not [string]::IsNullOrWhiteSpace($inputName)) {
        $IMAGE_NAME = $inputName
    }

    $inputVersion = Read-Host "Website image version [$IMAGE_VERSION]"
    if (-not [string]::IsNullOrWhiteSpace($inputVersion)) {
        $IMAGE_VERSION = $inputVersion
    }
    if ([string]::IsNullOrWhiteSpace($IMAGE_VERSION)) {
        $IMAGE_VERSION = "latest"
    }

    $FULL_IMAGE = "${IMAGE_NAME}:${IMAGE_VERSION}"

    $TargetPlatform = $env:TARGET_PLATFORM
    if ([string]::IsNullOrWhiteSpace($TargetPlatform)) {
        $TargetPlatform = "linux/amd64"
    }

    $useBuildx = $false
    try {
        docker buildx version | Out-Null
        if ($LASTEXITCODE -eq 0) { $useBuildx = $true }
    } catch {
        $useBuildx = $false
    }

    Write-Host "" 
    Write-Host "[BUILD] Building: $FULL_IMAGE" -ForegroundColor Cyan
    Write-Host "Target platform: $TargetPlatform" -ForegroundColor Gray

    if ($useBuildx) {
        docker buildx build --platform $TargetPlatform -t $FULL_IMAGE -f Dockerfile_web --build-arg "WEB_IMAGE_TAG=$IMAGE_VERSION" --load .
    } else {
        docker build -t $FULL_IMAGE -f Dockerfile_web --build-arg "WEB_IMAGE_TAG=$IMAGE_VERSION" .
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Build failed" -ForegroundColor Red
        return
    }

    Write-Host "[PUSH] Pushing image to registry..." -ForegroundColor Cyan
    docker push $FULL_IMAGE
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Push failed" -ForegroundColor Red
        return
    }
    Write-Host "[OK] Image pushed: $FULL_IMAGE" -ForegroundColor Green

    if ($IMAGE_VERSION -ne "latest") {
        docker tag $FULL_IMAGE "${IMAGE_NAME}:latest"
        docker push "${IMAGE_NAME}:latest"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Failed to push ${IMAGE_NAME}:latest" -ForegroundColor Red
            return
        }
        Write-Host "[OK] Also pushed: ${IMAGE_NAME}:latest" -ForegroundColor Green
    }

    if (Test-Path .env) {
        $envLines = Get-Content .env -ErrorAction SilentlyContinue

        $hasName = $false
        $hasVersion = $false
        $newLines = @()

        foreach ($line in $envLines) {
            if ($line -match '^WEB_IMAGE_NAME=') {
                $newLines += "WEB_IMAGE_NAME=$IMAGE_NAME"
                $hasName = $true
            } elseif ($line -match '^WEB_IMAGE_VERSION=') {
                $newLines += "WEB_IMAGE_VERSION=$IMAGE_VERSION"
                $hasVersion = $true
            } else {
                $newLines += $line
            }
        }

        if (-not $hasName) { $newLines += "WEB_IMAGE_NAME=$IMAGE_NAME" }
        if (-not $hasVersion) { $newLines += "WEB_IMAGE_VERSION=$IMAGE_VERSION" }

        $newLines | Set-Content .env -Encoding utf8
        Write-Host "[OK] Updated .env with WEB_IMAGE_NAME=$IMAGE_NAME, WEB_IMAGE_VERSION=$IMAGE_VERSION" -ForegroundColor Green
    }
}

function Start-StackDetachedWithTelegram {
    <#
    .SYNOPSIS
        Start the local stack in detached mode including the Telegram admin bot listener.

    .PARAMETER ComposeFile
        Compose file path.
    #>

    param([string]$ComposeFile)

    Write-Host "[START] Starting Statechecker stack (detached, with telegram listener)..." -ForegroundColor Cyan
    Write-Host ""
    if (Get-Command Show-RelevantPagesDelayed -ErrorAction SilentlyContinue) {
        Show-RelevantPagesDelayed -ComposeFile $ComposeFile -TimeoutSeconds 120
    }
    docker compose --env-file .env -f $ComposeFile --profile telegram up --build -d
    Write-Host ""
    Write-Host "[OK] Services started in background" -ForegroundColor Green
    Write-Host "View logs with: docker compose --env-file .env -f $ComposeFile logs -f" -ForegroundColor Gray
}

function Start-StackDetachedWithTelegramAndWeb {
    <#
    .SYNOPSIS
        Start the local stack detached including Telegram admin bot listener and nginx web.

    .PARAMETER ComposeFile
        Compose file path.
    #>

    param([string]$ComposeFile)

    Write-Host "[START] Starting Statechecker stack (detached, with telegram listener + web)..." -ForegroundColor Cyan
    Write-Host ""
    if (Get-Command Show-RelevantPagesDelayed -ErrorAction SilentlyContinue) {
        Show-RelevantPagesDelayed -ComposeFile $ComposeFile -TimeoutSeconds 120
    }
    docker compose --env-file .env -f $ComposeFile --profile telegram --profile web up --build -d
    Write-Host ""
    Write-Host "[OK] Services started in background" -ForegroundColor Green
    Write-Host "View logs with: docker compose --env-file .env -f $ComposeFile logs -f" -ForegroundColor Gray
}

function Start-Stack {
    <#
    .SYNOPSIS
        Start the local stack in foreground.

    .PARAMETER ComposeFile
        Compose file path.
    #>

    param([string]$ComposeFile)
    
    Write-Host "[START] Starting Statechecker stack..." -ForegroundColor Cyan
    Write-Host ""
    if (Get-Command Show-RelevantPagesDelayed -ErrorAction SilentlyContinue) {
        Show-RelevantPagesDelayed -ComposeFile $ComposeFile -TimeoutSeconds 120
    }
    docker compose --env-file .env -f $ComposeFile up --build
}

function Start-StackWithTelegram {
    <#
    .SYNOPSIS
        Start the local stack in foreground including the Telegram admin bot listener.

    .PARAMETER ComposeFile
        Compose file path.
    #>

    param([string]$ComposeFile)

    Write-Host "[START] Starting Statechecker stack (with telegram listener)..." -ForegroundColor Cyan
    Write-Host ""
    if (Get-Command Show-RelevantPagesDelayed -ErrorAction SilentlyContinue) {
        Show-RelevantPagesDelayed -ComposeFile $ComposeFile -TimeoutSeconds 120
    }
    docker compose --env-file .env -f $ComposeFile --profile telegram up --build
}

function Start-StackWithTelegramAndWeb {
    <#
    .SYNOPSIS
        Start the local stack in foreground including Telegram admin bot listener and nginx web.

    .PARAMETER ComposeFile
        Compose file path.
    #>

    param([string]$ComposeFile)

    Write-Host "[START] Starting Statechecker stack (with telegram listener + web)..." -ForegroundColor Cyan
    Write-Host ""
    if (Get-Command Show-RelevantPagesDelayed -ErrorAction SilentlyContinue) {
        Show-RelevantPagesDelayed -ComposeFile $ComposeFile -TimeoutSeconds 120
    }
    docker compose --env-file .env -f $ComposeFile --profile telegram --profile web up --build
}

function Start-StackDetached {
    <#
    .SYNOPSIS
        Start the local stack in detached mode.

    .PARAMETER ComposeFile
        Compose file path.
    #>

    param([string]$ComposeFile)
    
    Write-Host "[START] Starting Statechecker stack (detached)..." -ForegroundColor Cyan
    Write-Host ""
    if (Get-Command Show-RelevantPagesDelayed -ErrorAction SilentlyContinue) {
        Show-RelevantPagesDelayed -ComposeFile $ComposeFile -TimeoutSeconds 120
    }
    docker compose --env-file .env -f $ComposeFile up --build -d
    Write-Host ""
    Write-Host "[OK] Services started in background" -ForegroundColor Green
    Write-Host "View logs with: docker compose --env-file .env -f $ComposeFile logs -f" -ForegroundColor Gray
}

function Invoke-DockerComposeDown {
    <#
    .SYNOPSIS
        Stop the local stack.

    .PARAMETER ComposeFile
        Compose file path.
    #>

    param([string]$ComposeFile)
    
    Write-Host "[STOP] Stopping containers..." -ForegroundColor Yellow
    Write-Host "   Using compose file: $ComposeFile" -ForegroundColor Gray
    Write-Host ""
    docker compose --env-file .env -f $ComposeFile down
    Write-Host ""
    Write-Host "[OK] Containers stopped" -ForegroundColor Green
}

function Build-ProductionImage {
    <#
    .SYNOPSIS
        Build the production Docker image using build-image scripts.
    #>

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
    <#
    .SYNOPSIS
        Tail docker compose logs.

    .PARAMETER ComposeFile
        Compose file path.
    #>

    param([string]$ComposeFile)
    
    Write-Host "[LOGS] Viewing logs..." -ForegroundColor Cyan
    docker compose --env-file .env -f $ComposeFile logs -f
}

function Invoke-DbReinstall {
    <#
    .SYNOPSIS
        Reinstall the database by moving db_data aside and reinitializing schema/backup.

    .PARAMETER ComposeFile
        Compose file path.
    #>

    param([string]$ComposeFile)
    Invoke-DbReinstallInteractive -ComposeFile $ComposeFile -ProjectName "Statechecker" -SchemaFilename "state_checker.sql"
}

function Show-MainMenu {
    <#
    .SYNOPSIS
        Show the interactive quick-start menu.

    .PARAMETER ComposeFile
        Compose file path.
    #>

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
    $MENU_BUILD_WEB_IMAGE = $menuNext; $menuNext++

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
    Write-Host "  $MENU_EXIT) Exit" -ForegroundColor Gray
    Write-Host "" 
    $choice = Read-Host "Your choice (1-$MENU_EXIT)"

    switch ($choice) {
        "$MENU_RUN_START" {
            Start-StackWithTelegramAndWeb -ComposeFile $ComposeFile
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
