<#
.SYNOPSIS
    Build operations module for Statechecker quick-start menu.

.DESCRIPTION
    This module provides functions for building Docker images for Statechecker.
    Extracted from menu_handlers.ps1 for single responsibility and modularity.

.NOTES
    Author: Auto-generated
    Date: 2026-01-29
    Version: 1.0.0
#>

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
