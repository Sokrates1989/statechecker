<#
.SYNOPSIS
    Keycloak operations module for Statechecker quick-start menu.

.DESCRIPTION
    This module provides functions for Keycloak-related operations including
    bootstrap, token retrieval, and realm management for Statechecker.

.NOTES
    Author: Auto-generated
    Date: 2026-01-29
    Version: 1.0.0
#>

function Get-EnvVariable {
    <#
    .SYNOPSIS
        Get an environment variable from .env file or environment.

    .PARAMETER VariableName
        Name of the variable to retrieve.

    .PARAMETER EnvFile
        Path to the .env file.

    .PARAMETER DefaultValue
        Default value if not found.

    .RETURNS
        The variable value or default.
    #>
    param(
        [string]$VariableName,
        [string]$EnvFile = ".env",
        [string]$DefaultValue = ""
    )

    $value = $DefaultValue

    if (Test-Path $EnvFile) {
        $envContent = Get-Content $EnvFile -ErrorAction SilentlyContinue
        $line = $envContent | Where-Object { $_ -match "^$VariableName=" }
        if ($line) {
            $value = ($line -split "=", 2)[1].Trim().Trim('"')
        }
    }

    if ([string]::IsNullOrWhiteSpace($value)) {
        $envValue = [Environment]::GetEnvironmentVariable($VariableName)
        if (-not [string]::IsNullOrWhiteSpace($envValue)) {
            $value = $envValue
        }
    }

    return $value
}

function Get-KeycloakAccessToken {
    <#
    .SYNOPSIS
        Retrieve a Keycloak access token using client credentials.

    .PARAMETER EnvFile
        Path to the environment file to read KEYCLOAK_* variables from.

    .RETURNS
        Access token string.
    #>
    param(
        [string]$EnvFile = ".env"
    )

    $accessToken = $env:ACCESS_TOKEN
    if ($accessToken) {
        return $accessToken
    }

    $keycloakUrl = Get-EnvVariable -VariableName "KEYCLOAK_URL" -EnvFile $EnvFile -DefaultValue ""
    $keycloakRealm = Get-EnvVariable -VariableName "KEYCLOAK_REALM" -EnvFile $EnvFile -DefaultValue ""
    $keycloakClientId = Get-EnvVariable -VariableName "KEYCLOAK_CLIENT_ID" -EnvFile $EnvFile -DefaultValue ""
    $keycloakClientSecret = Get-EnvVariable -VariableName "KEYCLOAK_CLIENT_SECRET" -EnvFile $EnvFile -DefaultValue ""

    if ($keycloakUrl -and $keycloakRealm -and $keycloakClientId -and $keycloakClientSecret) {
        $tokenEndpoint = "$($keycloakUrl.TrimEnd('/'))/realms/$keycloakRealm/protocol/openid-connect/token"
        $body = @{ 
            grant_type = "client_credentials"
            client_id = $keycloakClientId
            client_secret = $keycloakClientSecret
        }
        try {
            $tokenResponse = Invoke-RestMethod -Method Post -Uri $tokenEndpoint -Body $body -ContentType "application/x-www-form-urlencoded" -ErrorAction Stop
            if ($tokenResponse.access_token) {
                return $tokenResponse.access_token
            }
        } catch {
            Write-Host "[WARN] Failed to fetch Keycloak access token: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }

    return Read-Host "Enter Keycloak access token"
}

function Invoke-KeycloakBootstrap {
    <#
    .SYNOPSIS
        Bootstrap Keycloak realm, clients, roles, and users for Statechecker.

    .DESCRIPTION
        This function:
        - Checks if Keycloak is reachable
        - Collects configuration from user
        - Creates realm, clients, roles, and users

    .RETURNS
        0 on success, 1 on failure.
    #>

    $projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
    
    Write-Host "[KEYCLOAK] Keycloak Bootstrap for Statechecker" -ForegroundColor Cyan
    Write-Host ""
    
    # Load .env defaults
    $keycloakUrl = Get-EnvVariable -VariableName "KEYCLOAK_URL" -EnvFile "$projectRoot\.env" -DefaultValue "http://localhost:9090"
    $keycloakRealm = Get-EnvVariable -VariableName "KEYCLOAK_REALM" -EnvFile "$projectRoot\.env" -DefaultValue "statechecker"
    
    # Check if Keycloak is reachable
    Write-Host "[CHECK] Checking Keycloak at $keycloakUrl..." -ForegroundColor Cyan
    try {
        $null = Invoke-WebRequest -Uri "$keycloakUrl/" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        Write-Host "[OK] Keycloak is reachable" -ForegroundColor Green
    } catch {
        Write-Host ""
        Write-Host "[ERROR] Cannot reach Keycloak at $keycloakUrl" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please ensure Keycloak is running. Start it from the dedicated repo:" -ForegroundColor Yellow
        Write-Host "  https://github.com/Sokrates1989/keycloak.git" -ForegroundColor Gray
        Write-Host ""
        return 1
    }
    Write-Host ""
    
    # Collect configuration
    $inputUrl = Read-Host "Keycloak base URL [$keycloakUrl]"
    if (-not [string]::IsNullOrWhiteSpace($inputUrl)) {
        $keycloakUrl = $inputUrl
    }
    
    $adminUser = Read-Host "Keycloak admin username [admin]"
    if ([string]::IsNullOrWhiteSpace($adminUser)) {
        $adminUser = "admin"
    }
    
    $adminPassword = Read-Host "Keycloak admin password [admin]"
    if ([string]::IsNullOrWhiteSpace($adminPassword)) {
        $adminPassword = "admin"
    }
    
    $realm = Read-Host "Realm name [$keycloakRealm]"
    if ([string]::IsNullOrWhiteSpace($realm)) {
        $realm = $keycloakRealm
    }
    
    $frontendClient = Read-Host "Frontend client ID [statechecker-frontend]"
    if ([string]::IsNullOrWhiteSpace($frontendClient)) {
        $frontendClient = "statechecker-frontend"
    }
    
    $backendClient = Read-Host "Backend client ID [statechecker-backend]"
    if ([string]::IsNullOrWhiteSpace($backendClient)) {
        $backendClient = "statechecker-backend"
    }
    
    $webPort = Get-EnvVariable -VariableName "WEB_PORT" -EnvFile "$projectRoot\.env" -DefaultValue "8788"
    $frontendUrl = Read-Host "Frontend root URL [http://localhost:$webPort]"
    if ([string]::IsNullOrWhiteSpace($frontendUrl)) {
        $frontendUrl = "http://localhost:$webPort"
    }
    
    $apiPort = Get-EnvVariable -VariableName "REST_API_PORT" -EnvFile "$projectRoot\.env" -DefaultValue "8787"
    $apiUrl = Read-Host "API root URL [http://localhost:$apiPort]"
    if ([string]::IsNullOrWhiteSpace($apiUrl)) {
        $apiUrl = "http://localhost:$apiPort"
    }
    
    Write-Host ""
    Write-Host "[INFO] Creating roles:" -ForegroundColor Cyan
    Write-Host "   - statechecker:admin (full access)" -ForegroundColor Gray
    Write-Host "   - statechecker:read  (view-only access)" -ForegroundColor Gray
    Write-Host ""
    
    $createAdmin = Read-Host "Create default admin user? (Y/n)"
    $adminUsername = ""
    $adminEmail = ""
    $adminUserpass = ""
    
    if ($createAdmin -notmatch "^[Nn]$") {
        $adminUsername = Read-Host "Admin username [admin]"
        if ([string]::IsNullOrWhiteSpace($adminUsername)) {
            $adminUsername = "admin"
        }
        
        $adminEmail = Read-Host "Admin email [admin@example.com]"
        if ([string]::IsNullOrWhiteSpace($adminEmail)) {
            $adminEmail = "admin@example.com"
        }
        
        $adminUserpass = Read-Host "Admin password [admin]"
        if ([string]::IsNullOrWhiteSpace($adminUserpass)) {
            $adminUserpass = "admin"
        }
    }
    
    Write-Host ""
    Write-Host "[BOOTSTRAP] Bootstrapping Keycloak realm..." -ForegroundColor Cyan
    
    # Get admin token
    $tokenEndpoint = "$($keycloakUrl.TrimEnd('/'))/realms/master/protocol/openid-connect/token"
    $body = @{
        grant_type = "password"
        client_id = "admin-cli"
        username = $adminUser
        password = $adminPassword
    }
    
    try {
        $tokenResponse = Invoke-RestMethod -Method Post -Uri $tokenEndpoint -Body $body -ContentType "application/x-www-form-urlencoded" -ErrorAction Stop
        $accessToken = $tokenResponse.access_token
    } catch {
        Write-Host "[ERROR] Failed to get admin token. Check credentials." -ForegroundColor Red
        return 1
    }
    
    Write-Host "[OK] Got admin token" -ForegroundColor Green
    
    $headers = @{
        Authorization = "Bearer $accessToken"
        "Content-Type" = "application/json"
    }
    
    # Create realm if it doesn't exist
    try {
        $null = Invoke-RestMethod -Uri "$($keycloakUrl.TrimEnd('/'))/admin/realms/$realm" -Headers $headers -ErrorAction Stop
        Write-Host "[INFO] Realm $realm already exists" -ForegroundColor Gray
    } catch {
        if ($_.Exception.Response.StatusCode -eq 404) {
            Write-Host "[CREATE] Creating realm: $realm" -ForegroundColor Cyan
            $realmBody = @{
                realm = $realm
                enabled = $true
            } | ConvertTo-Json
            Invoke-RestMethod -Method Post -Uri "$($keycloakUrl.TrimEnd('/'))/admin/realms" -Headers $headers -Body $realmBody -ErrorAction SilentlyContinue
        }
    }
    
    # Create frontend client (public)
    Write-Host "[CREATE] Creating frontend client: $frontendClient" -ForegroundColor Cyan
    $frontendClientBody = @{
        clientId = $frontendClient
        enabled = $true
        publicClient = $true
        directAccessGrantsEnabled = $true
        standardFlowEnabled = $true
        redirectUris = @("$frontendUrl/*")
        webOrigins = @($frontendUrl, $apiUrl)
    } | ConvertTo-Json
    try {
        Invoke-RestMethod -Method Post -Uri "$($keycloakUrl.TrimEnd('/'))/admin/realms/$realm/clients" -Headers $headers -Body $frontendClientBody -ErrorAction SilentlyContinue
    } catch { }
    
    # Create backend client (confidential)
    Write-Host "[CREATE] Creating backend client: $backendClient" -ForegroundColor Cyan
    $backendClientBody = @{
        clientId = $backendClient
        enabled = $true
        publicClient = $false
        serviceAccountsEnabled = $true
        directAccessGrantsEnabled = $true
        standardFlowEnabled = $false
    } | ConvertTo-Json
    try {
        Invoke-RestMethod -Method Post -Uri "$($keycloakUrl.TrimEnd('/'))/admin/realms/$realm/clients" -Headers $headers -Body $backendClientBody -ErrorAction SilentlyContinue
    } catch { }
    
    # Get backend client secret
    $clientSecret = ""
    try {
        $clientsResponse = Invoke-RestMethod -Uri "$($keycloakUrl.TrimEnd('/'))/admin/realms/$realm/clients?clientId=$backendClient" -Headers $headers -ErrorAction Stop
        if ($clientsResponse -and $clientsResponse.Count -gt 0) {
            $backendId = $clientsResponse[0].id
            $secretResponse = Invoke-RestMethod -Uri "$($keycloakUrl.TrimEnd('/'))/admin/realms/$realm/clients/$backendId/client-secret" -Headers $headers -ErrorAction Stop
            $clientSecret = $secretResponse.value
        }
    } catch { }
    
    # Create roles
    Write-Host "[CREATE] Creating roles..." -ForegroundColor Cyan
    foreach ($role in @("statechecker:admin", "statechecker:read")) {
        $roleBody = @{ name = $role } | ConvertTo-Json
        try {
            Invoke-RestMethod -Method Post -Uri "$($keycloakUrl.TrimEnd('/'))/admin/realms/$realm/roles" -Headers $headers -Body $roleBody -ErrorAction SilentlyContinue
        } catch { }
    }
    
    # Create admin user if requested
    if (-not [string]::IsNullOrWhiteSpace($adminUsername)) {
        Write-Host "[CREATE] Creating user: $adminUsername" -ForegroundColor Cyan
        $userBody = @{
            username = $adminUsername
            email = $adminEmail
            enabled = $true
            emailVerified = $true
            credentials = @(@{
                type = "password"
                value = $adminUserpass
                temporary = $false
            })
        } | ConvertTo-Json -Depth 3
        try {
            Invoke-RestMethod -Method Post -Uri "$($keycloakUrl.TrimEnd('/'))/admin/realms/$realm/users" -Headers $headers -Body $userBody -ErrorAction SilentlyContinue
        } catch { }
        
        # Get user ID and assign role
        try {
            $usersResponse = Invoke-RestMethod -Uri "$($keycloakUrl.TrimEnd('/'))/admin/realms/$realm/users?username=$adminUsername" -Headers $headers -ErrorAction Stop
            if ($usersResponse -and $usersResponse.Count -gt 0) {
                $userId = $usersResponse[0].id
                
                # Get role
                $roleResponse = Invoke-RestMethod -Uri "$($keycloakUrl.TrimEnd('/'))/admin/realms/$realm/roles/statechecker:admin" -Headers $headers -ErrorAction Stop
                
                $roleMapping = @(@{
                    id = $roleResponse.id
                    name = $roleResponse.name
                }) | ConvertTo-Json
                
                Invoke-RestMethod -Method Post -Uri "$($keycloakUrl.TrimEnd('/'))/admin/realms/$realm/users/$userId/role-mappings/realm" -Headers $headers -Body $roleMapping -ErrorAction SilentlyContinue
                Write-Host "[OK] Assigned statechecker:admin role to $adminUsername" -ForegroundColor Green
            }
        } catch { }
    }
    
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Yellow
    Write-Host "[OK] Bootstrap complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Update your .env with these values:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "   KEYCLOAK_ENABLED=true" -ForegroundColor Gray
    Write-Host "   KEYCLOAK_URL=$keycloakUrl" -ForegroundColor Gray
    Write-Host "   KEYCLOAK_REALM=$realm" -ForegroundColor Gray
    Write-Host "   KEYCLOAK_CLIENT_ID=$frontendClient" -ForegroundColor Gray
    Write-Host "   KEYCLOAK_BACKEND_CLIENT_ID=$backendClient" -ForegroundColor Gray
    if (-not [string]::IsNullOrWhiteSpace($clientSecret)) {
        Write-Host "   KEYCLOAK_CLIENT_SECRET=$clientSecret" -ForegroundColor Gray
    }
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Yellow
    
    return 0
}
