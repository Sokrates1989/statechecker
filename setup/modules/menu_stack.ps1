<#
.SYNOPSIS
    Stack operations module for Statechecker quick-start menu.

.DESCRIPTION
    This module provides functions for starting, stopping, and managing
    the Docker Compose stack for Statechecker. Extracted from menu_handlers.ps1
    for single responsibility and modularity.

.NOTES
    Author: Auto-generated
    Date: 2026-01-29
    Version: 1.0.0
#>

$scriptPath = $PSScriptRoot
$browserHelpersPath = Join-Path $scriptPath "browser_helpers.ps1"
if (Test-Path $browserHelpersPath) {
    . $browserHelpersPath
}

function Start-Stack {
    <#
    .SYNOPSIS
        Start the local stack in foreground.

    .PARAMETER ComposeFile
        Path to the Docker Compose file.
    #>
    param([string]$ComposeFile)
    
    Write-Host "[START] Starting Statechecker stack..." -ForegroundColor Cyan
    Write-Host ""
    if (Get-Command Show-RelevantPagesDelayed -ErrorAction SilentlyContinue) {
        Show-RelevantPagesDelayed -ComposeFile $ComposeFile -TimeoutSeconds 120
    }
    docker compose --env-file .env -f $ComposeFile up --build
}

function Start-StackDetached {
    <#
    .SYNOPSIS
        Start the local stack in detached mode.

    .PARAMETER ComposeFile
        Path to the Docker Compose file.
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

function Start-StackWithTelegram {
    <#
    .SYNOPSIS
        Start the local stack in foreground including the Telegram admin bot listener.

    .PARAMETER ComposeFile
        Path to the Docker Compose file.
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
        Path to the Docker Compose file.

    .PARAMETER LogToFile
        If specified, logs Docker Compose container logs to a timestamped file via docker compose logs -f.
    #>
    param(
        [string]$ComposeFile,
        [switch]$LogToFile
    )

    Write-Host "[START] Starting Statechecker stack (with telegram listener + web)..." -ForegroundColor Cyan
    Write-Host ""

    $projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
    $envFilePath = (Resolve-Path ".env").Path

    if ($LogToFile) {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $logDir = Join-Path $projectRoot (Join-Path "logs" (Join-Path "stack" $timestamp))
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        $composeLogFile = Join-Path $logDir "docker-compose.log"
        Set-Content -Path $composeLogFile -Value "" -Encoding utf8
        Write-Host "[LOG] Writing docker-compose container logs to: $composeLogFile" -ForegroundColor Gray
    }

    if (Get-Command Show-RelevantPagesDelayed -ErrorAction SilentlyContinue) {
        Show-RelevantPagesDelayed -ComposeFile $ComposeFile -TimeoutSeconds 120
    }

    $composeArgsBase = @(
        "--ansi", "never",
        "--progress", "plain",
        "--env-file", $envFilePath,
        "-f", $ComposeFile,
        "--profile", "telegram",
        "--profile", "web"
    )

    if ($LogToFile) {
        # Start a background job to capture container logs via docker compose logs -f
        $logJob = Start-Job -ScriptBlock {
            param($ProjectRoot, $LogFile, $ComposeArgsBase)

            Set-Location $ProjectRoot

            try {
                Add-Content -Path $LogFile -Value ("[{0}] docker compose logs -f started" -f (Get-Date)) -Encoding utf8
                Add-Content -Path $LogFile -Value ("[{0}] Compose args: {1}" -f (Get-Date), ($ComposeArgsBase -join " ")) -Encoding utf8
            } catch { }

            # Wait for at least one container to be running
            $deadline = (Get-Date).AddSeconds(60)
            $attempts = 0
            while ((Get-Date) -lt $deadline) {
                try {
                    $running = & docker compose @ComposeArgsBase ps --services --filter status=running 2>$null
                    Add-Content -Path $LogFile -Value ("[{0}] Checking for running containers (attempt {1}): {2}" -f (Get-Date), $attempts, ($running -join ", ")) -Encoding utf8
                    if ($running -and $running.Count -gt 0) {
                        Add-Content -Path $LogFile -Value ("[{0}] Found running containers: {1}" -f (Get-Date), ($running -join ", ")) -Encoding utf8
                        break
                    }
                } catch {
                    Add-Content -Path $LogFile -Value ("[{0}] Error checking running containers: {1}" -f (Get-Date), $_.Exception.Message) -Encoding utf8
                }
                $attempts++
                Start-Sleep -Seconds 1
            }
            
            if ((Get-Date) -ge $deadline) {
                Add-Content -Path $LogFile -Value ("[{0}] Timeout waiting for running containers after {1} attempts" -f (Get-Date), $attempts) -Encoding utf8
            }

            try {
                & docker compose @ComposeArgsBase logs -f --no-color 2>&1 | ForEach-Object {
                    try { Add-Content -Path $LogFile -Value $_ -Encoding utf8 } catch { }
                }
            } finally {
                try {
                    Add-Content -Path $LogFile -Value ("[{0}] docker compose logs -f stopped" -f (Get-Date)) -Encoding utf8
                } catch { }
            }
        } -ArgumentList $projectRoot, $composeLogFile, $composeArgsBase

        try {
            & docker compose @composeArgsBase up --build
        } finally {
            try { Stop-Job -Job $logJob -Force -ErrorAction SilentlyContinue } catch { }
            try { Remove-Job -Job $logJob -Force -ErrorAction SilentlyContinue } catch { }
        }
    } else {
        docker compose --env-file .env -f $ComposeFile --profile telegram --profile web up --build
    }
}

function Start-StackDetachedWithTelegram {
    <#
    .SYNOPSIS
        Start the local stack in detached mode including the Telegram admin bot listener.

    .PARAMETER ComposeFile
        Path to the Docker Compose file.
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
        Path to the Docker Compose file.
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

function Invoke-DockerComposeDown {
    <#
    .SYNOPSIS
        Stop the local stack.

    .PARAMETER ComposeFile
        Path to the Docker Compose file.
    #>
    param([string]$ComposeFile)
    
    Write-Host "[STOP] Stopping containers..." -ForegroundColor Yellow
    Write-Host "   Using compose file: $ComposeFile" -ForegroundColor Gray
    Write-Host ""
    docker compose --env-file .env -f $ComposeFile down --remove-orphans
    Write-Host ""
    Write-Host "[OK] Containers stopped" -ForegroundColor Green
}

function Show-Logs {
    <#
    .SYNOPSIS
        Tail docker compose logs.

    .PARAMETER ComposeFile
        Path to the Docker Compose file.
    #>
    param([string]$ComposeFile)
    
    Write-Host "[LOGS] Viewing logs..." -ForegroundColor Cyan
    docker compose --env-file .env -f $ComposeFile logs -f
}
