# quick-start.ps1
# Quick start tool for Statechecker

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$setupDir = Join-Path $scriptDir "setup"

 $dbHelpersPath = Join-Path $setupDir "modules\db_helpers.ps1"
 if (Test-Path $dbHelpersPath) {
     . $dbHelpersPath
 }

# Import modules
Import-Module "$setupDir\modules\docker_helpers.ps1" -Force
Import-Module "$setupDir\modules\browser_helpers.ps1" -Force
Import-Module "$setupDir\modules\menu_handlers.ps1" -Force

Write-Host "Statechecker - Quick Start" -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Cyan
Write-Host ""

# Check Docker availability
if (-not (Test-DockerInstallation)) {
    exit 1
}
Write-Host ""

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "[WARN] .env file not found" -ForegroundColor Yellow
    Write-Host ""
    if (Test-Path setup\.env.template) {
        $createEnv = Read-Host "Create .env from template? (Y/n)"
        if ($createEnv -ne "n" -and $createEnv -ne "N") {
            Copy-Item setup\.env.template .env
            Write-Host "[OK] .env created from template" -ForegroundColor Green
            Write-Host "[WARN] Please edit .env with your configuration before continuing" -ForegroundColor Yellow
            Write-Host ""
            $editor = $env:EDITOR
            if ([string]::IsNullOrWhiteSpace($editor)) { $editor = "notepad" }
            $openNow = Read-Host "Open .env now in $editor? (Y/n)"
            if ($openNow -notmatch "^[Nn]$") {
                & $editor ".env"
            }
            $null = Read-Host "Press Enter to continue after editing .env..."
        } else {
            Write-Host "[ERROR] Cannot continue without .env file" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "[ERROR] setup\.env.template not found!" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
}

# Determine compose file
$COMPOSE_FILE = "local-deployment\docker-compose.yml"

if (-not (Test-Path $COMPOSE_FILE)) {
    Write-Host "[WARN] $COMPOSE_FILE not found" -ForegroundColor Yellow
}

Write-Host "Using compose file: $COMPOSE_FILE" -ForegroundColor Cyan
Write-Host ""

 # Only prompt for DB init on first setup (empty db_data)
 if ($COMPOSE_FILE -eq "local-deployment\docker-compose.yml" -and (Test-Path $COMPOSE_FILE)) {
     if (Test-DbDataEmpty -ProjectRoot $scriptDir) {
         $dbInitSource = Invoke-PromptDbInitMode -ProjectRoot $scriptDir
         Set-DbInitSource -ComposePath $COMPOSE_FILE -InitSource $dbInitSource -SchemaFilename "state_checker.sql"
         Write-Host ""
     }
 }

# Show main menu
Show-MainMenu -ComposeFile $COMPOSE_FILE
