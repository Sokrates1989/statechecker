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

function Build-AllImages {
    <#
    .SYNOPSIS
        Build both the production API image and the website image.
        Prompts once for version, then builds and pushes both images.
    #>

    Write-Host "[BUILD] Building all Docker images (API + Web)..." -ForegroundColor Cyan
    Write-Host ""

    # Get version for both images
    $API_IMAGE_NAME = "sokrates1989/statechecker"
    $WEB_IMAGE_NAME = "sokrates1989/statechecker-web"
    $API_IMAGE_VERSION = "latest"
    $WEB_IMAGE_VERSION = "latest"

    # Read current values from .env
    if (Test-Path .env) {
        $envContent = Get-Content .env -ErrorAction SilentlyContinue

        $apiNameLine = $envContent | Where-Object { $_ -match "^IMAGE_NAME=" }
        if ($apiNameLine) {
            $API_IMAGE_NAME = ($apiNameLine -split "=", 2)[1].Trim().Trim('"')
        }

        $apiVersionLine = $envContent | Where-Object { $_ -match "^IMAGE_VERSION=" }
        if ($apiVersionLine) {
            $API_IMAGE_VERSION = ($apiVersionLine -split "=", 2)[1].Trim().Trim('"')
        }

        $webNameLine = $envContent | Where-Object { $_ -match "^WEB_IMAGE_NAME=" }
        if ($webNameLine) {
            $WEB_IMAGE_NAME = ($webNameLine -split "=", 2)[1].Trim().Trim('"')
        }

        $webVersionLine = $envContent | Where-Object { $_ -match "^WEB_IMAGE_VERSION=" }
        if ($webVersionLine) {
            $WEB_IMAGE_VERSION = ($webVersionLine -split "=", 2)[1].Trim().Trim('"')
        }
    }

    # Use API version as default for both images
    $defaultVersion = if ($API_IMAGE_VERSION -ne "latest") { $API_IMAGE_VERSION } else { $WEB_IMAGE_VERSION }
    if ($defaultVersion -eq "latest") {
        # Try to get from .ci.env as fallback
        if (Test-Path .ci.env) {
            $ciEnvContent = Get-Content .ci.env -ErrorAction SilentlyContinue
            $ciVersionLine = $ciEnvContent | Where-Object { $_ -match "^IMAGE_VERSION=" }
            if ($ciVersionLine) {
                $defaultVersion = ($ciVersionLine -split "=", 2)[1].Trim().Trim('"')
            }
        }
    }

    # Prompt for version once
    $inputVersion = Read-Host "Image version for both API and Web [$defaultVersion]"
    if (-not [string]::IsNullOrWhiteSpace($inputVersion)) {
        $API_IMAGE_VERSION = $inputVersion
        $WEB_IMAGE_VERSION = $inputVersion
    } else {
        $API_IMAGE_VERSION = $defaultVersion
        $WEB_IMAGE_VERSION = $defaultVersion
    }
    if ([string]::IsNullOrWhiteSpace($API_IMAGE_VERSION)) {
        $API_IMAGE_VERSION = "latest"
        $WEB_IMAGE_VERSION = "latest"
    }

    Write-Host ""
    Write-Host "Building with version: $API_IMAGE_VERSION" -ForegroundColor Cyan
    Write-Host "  - API: ${API_IMAGE_NAME}:${API_IMAGE_VERSION}" -ForegroundColor Gray
    Write-Host "  - Web: ${WEB_IMAGE_NAME}:${WEB_IMAGE_VERSION}" -ForegroundColor Gray
    Write-Host ""

    # Build API image first
    Write-Host "[BUILD] Building API image..." -ForegroundColor Cyan
    if (Test-Path "build-image\build-image.ps1") {
        & .\build-image\build-image.ps1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] API image build failed" -ForegroundColor Red
            return
        }
    } elseif (Test-Path "build-image\build-image.sh") {
        Write-Host "Running build-image.sh via bash..." -ForegroundColor Yellow
        bash build-image/build-image.sh
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] API image build failed" -ForegroundColor Red
            return
        }
    } else {
        Write-Host "[ERROR] build-image script not found" -ForegroundColor Red
        return
    }

    # Update .env with API version
    if (Test-Path .env) {
        $envLines = Get-Content .env -ErrorAction SilentlyContinue
        $newLines = @()
        $hasApiVersion = $false

        foreach ($line in $envLines) {
            if ($line -match '^IMAGE_VERSION=') {
                $newLines += "IMAGE_VERSION=$API_IMAGE_VERSION"
                $hasApiVersion = $true
            } else {
                $newLines += $line
            }
        }

        if (-not $hasApiVersion) { $newLines += "IMAGE_VERSION=$API_IMAGE_VERSION" }
        $newLines | Set-Content .env -Encoding utf8
        Write-Host "[OK] Updated .env with IMAGE_VERSION=$API_IMAGE_VERSION" -ForegroundColor Green
    }

    # Build web image
    Write-Host "[BUILD] Building Web image..." -ForegroundColor Cyan

    if (-not (Test-Path "Dockerfile_web")) {
        Write-Host "[ERROR] Dockerfile_web not found" -ForegroundColor Red
        return
    }

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

    $FULL_WEB_IMAGE = "${WEB_IMAGE_NAME}:${WEB_IMAGE_VERSION}"
    Write-Host "[BUILD] Building: $FULL_WEB_IMAGE" -ForegroundColor Cyan
    Write-Host "Target platform: $TargetPlatform" -ForegroundColor Gray

    if ($useBuildx) {
        docker buildx build --platform $TargetPlatform -t $FULL_WEB_IMAGE -f Dockerfile_web --build-arg "WEB_IMAGE_TAG=$WEB_IMAGE_VERSION" --load .
    } else {
        docker build -t $FULL_WEB_IMAGE -f Dockerfile_web --build-arg "WEB_IMAGE_TAG=$WEB_IMAGE_VERSION" .
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Web image build failed" -ForegroundColor Red
        return
    }

    # Push web image
    Write-Host "[PUSH] Pushing web image to registry..." -ForegroundColor Cyan
    docker push $FULL_WEB_IMAGE
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Web image push failed" -ForegroundColor Red
        return
    }
    Write-Host "[OK] Web image pushed: $FULL_WEB_IMAGE" -ForegroundColor Green

    if ($WEB_IMAGE_VERSION -ne "latest") {
        docker tag $FULL_WEB_IMAGE "${WEB_IMAGE_NAME}:latest"
        docker push "${WEB_IMAGE_NAME}:latest"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Failed to push ${WEB_IMAGE_NAME}:latest" -ForegroundColor Red
            return
        }
        Write-Host "[OK] Also pushed: ${WEB_IMAGE_NAME}:latest" -ForegroundColor Green
    }

    # Update .env with web version
    if (Test-Path .env) {
        $envLines = Get-Content .env -ErrorAction SilentlyContinue
        $newLines = @()
        $hasWebName = $false
        $hasWebVersion = $false

        foreach ($line in $envLines) {
            if ($line -match '^WEB_IMAGE_NAME=') {
                $newLines += "WEB_IMAGE_NAME=$WEB_IMAGE_NAME"
                $hasWebName = $true
            } elseif ($line -match '^WEB_IMAGE_VERSION=') {
                $newLines += "WEB_IMAGE_VERSION=$WEB_IMAGE_VERSION"
                $hasWebVersion = $true
            } else {
                $newLines += $line
            }
        }

        if (-not $hasWebName) { $newLines += "WEB_IMAGE_NAME=$WEB_IMAGE_NAME" }
        if (-not $hasWebVersion) { $newLines += "WEB_IMAGE_VERSION=$WEB_IMAGE_VERSION" }

        $newLines | Set-Content .env -Encoding utf8
        Write-Host "[OK] Updated .env with WEB_IMAGE_NAME=$WEB_IMAGE_NAME, WEB_IMAGE_VERSION=$WEB_IMAGE_VERSION" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "[SUCCESS] All images built and pushed successfully!" -ForegroundColor Green
    Write-Host "  - API: ${API_IMAGE_NAME}:${API_IMAGE_VERSION}" -ForegroundColor Gray
    Write-Host "  - Web: ${WEB_IMAGE_NAME}:${WEB_IMAGE_VERSION}" -ForegroundColor Gray
}
