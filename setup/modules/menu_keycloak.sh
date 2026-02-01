#!/bin/bash
#
# menu_keycloak.sh
#
# Module for Keycloak-related menu actions for Statechecker.
# This script provides functions to bootstrap Keycloak realm, clients, and users.
#

# Retrieve a Keycloak access token using client credentials.
#
# Returns:
#   Access token string.
get_keycloak_access_token() {
    local access_token="${ACCESS_TOKEN:-}"
    local keycloak_url="${KEYCLOAK_URL:-}"
    local keycloak_realm="${KEYCLOAK_REALM:-}"
    local keycloak_client_id="${KEYCLOAK_CLIENT_ID:-}"
    local keycloak_client_secret="${KEYCLOAK_CLIENT_SECRET:-}"

    if [ -f ".env" ]; then
        keycloak_url=$(grep "^KEYCLOAK_URL=" .env | head -n1 | cut -d'=' -f2- | tr -d ' "')
        keycloak_realm=$(grep "^KEYCLOAK_REALM=" .env | head -n1 | cut -d'=' -f2- | tr -d ' "')
        keycloak_client_id=$(grep "^KEYCLOAK_CLIENT_ID=" .env | head -n1 | cut -d'=' -f2- | tr -d ' "')
        keycloak_client_secret=$(grep "^KEYCLOAK_CLIENT_SECRET=" .env | head -n1 | cut -d'=' -f2- | tr -d ' "')
    fi

    if [ -z "$access_token" ] && [ -n "$keycloak_url" ] && [ -n "$keycloak_realm" ] && [ -n "$keycloak_client_id" ] && [ -n "$keycloak_client_secret" ]; then
        local token_endpoint="${keycloak_url%/}/realms/${keycloak_realm}/protocol/openid-connect/token"
        local token_response
        token_response=$(curl -s -X POST "$token_endpoint" \
            -H "Content-Type: application/x-www-form-urlencoded" \
            -d "grant_type=client_credentials" \
            -d "client_id=$keycloak_client_id" \
            -d "client_secret=$keycloak_client_secret")
        access_token=$(python3 -c "import json,sys; print(json.load(sys.stdin).get('access_token',''))" <<< "$token_response")
    fi

    if [ -z "$access_token" ]; then
        read_prompt "Enter Keycloak access token: " access_token
    fi

    echo "$access_token"
}

# Handle Keycloak bootstrap for Statechecker.
#
# This function:
# - Checks if Keycloak is reachable
# - Collects configuration from user
# - Creates realm, clients, roles, and users
#
# Returns:
#   0 on success, 1 on failure.
handle_keycloak_bootstrap() {
    local project_root
    project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    
    echo "🔐 Keycloak Bootstrap for Statechecker"
    echo ""
    
    # Load .env defaults
    local keycloak_url="${KEYCLOAK_URL:-http://localhost:9090}"
    local keycloak_realm="${KEYCLOAK_REALM:-statechecker}"
    if [ -f "$project_root/.env" ]; then
        keycloak_url=$(grep "^KEYCLOAK_URL=" "$project_root/.env" 2>/dev/null | head -n1 | cut -d'=' -f2- | tr -d ' "') || keycloak_url="http://localhost:9090"
        keycloak_realm=$(grep "^KEYCLOAK_REALM=" "$project_root/.env" 2>/dev/null | head -n1 | cut -d'=' -f2- | tr -d ' "') || keycloak_realm="statechecker"
    fi
    
    # Check if Keycloak is reachable
    echo "🔍 Checking Keycloak at $keycloak_url..."
    if ! curl -s --connect-timeout 5 "$keycloak_url/" >/dev/null 2>&1; then
        echo ""
        echo "❌ Cannot reach Keycloak at $keycloak_url"
        echo ""
        echo "Please ensure Keycloak is running. Start it from the dedicated repo:"
        echo "  https://github.com/Sokrates1989/keycloak.git"
        echo ""
        return 1
    fi
    echo "✅ Keycloak is reachable"
    echo ""
    
    # Collect configuration
    read_prompt "Keycloak base URL [$keycloak_url]: " input_url
    keycloak_url="${input_url:-$keycloak_url}"
    
    read_prompt "Keycloak admin username [admin]: " admin_user
    admin_user="${admin_user:-admin}"
    
    read_prompt "Keycloak admin password [admin]: " admin_password
    admin_password="${admin_password:-admin}"
    
    read_prompt "Realm name [$keycloak_realm]: " realm
    realm="${realm:-$keycloak_realm}"
    
    read_prompt "Frontend client ID [statechecker-frontend]: " frontend_client
    frontend_client="${frontend_client:-statechecker-frontend}"
    
    read_prompt "Backend client ID [statechecker-backend]: " backend_client
    backend_client="${backend_client:-statechecker-backend}"
    
    local web_port="${WEB_PORT:-8788}"
    read_prompt "Frontend root URL [http://localhost:$web_port]: " frontend_url
    frontend_url="${frontend_url:-http://localhost:$web_port}"
    
    local api_port="${REST_API_PORT:-8787}"
    read_prompt "API root URL [http://localhost:$api_port]: " api_url
    api_url="${api_url:-http://localhost:$api_port}"
    
    echo ""
    echo "✅ Creating roles:"
    echo "   - statechecker:admin (full access)"
    echo "   - statechecker:read  (view-only access)"
    echo ""
    
    read_prompt "Create default admin user? (Y/n): " create_admin
    local admin_username=""
    local admin_email=""
    local admin_userpass=""
    
    if [[ ! "$create_admin" =~ ^[Nn]$ ]]; then
        read_prompt "Admin username [admin]: " admin_username
        admin_username="${admin_username:-admin}"
        
        read_prompt "Admin email [admin@example.com]: " admin_email
        admin_email="${admin_email:-admin@example.com}"
        
        read_prompt "Admin password [admin]: " admin_userpass
        admin_userpass="${admin_userpass:-admin}"
    fi
    
    echo ""
    echo "🚀 Bootstrapping Keycloak realm..."
    
    # Get admin token
    local token_endpoint="${keycloak_url%/}/realms/master/protocol/openid-connect/token"
    local token_response
    token_response=$(curl -s -X POST "$token_endpoint" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "grant_type=password" \
        -d "client_id=admin-cli" \
        -d "username=$admin_user" \
        -d "password=$admin_password")
    
    local access_token
    access_token=$(python3 -c "import json,sys; print(json.load(sys.stdin).get('access_token',''))" <<< "$token_response" 2>/dev/null)
    
    if [ -z "$access_token" ]; then
        echo "❌ Failed to get admin token. Check credentials."
        return 1
    fi
    
    echo "✅ Got admin token"
    
    # Create realm if it doesn't exist
    local realm_check
    realm_check=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $access_token" \
        "${keycloak_url%/}/admin/realms/$realm")
    
    if [ "$realm_check" = "404" ]; then
        echo "📦 Creating realm: $realm"
        curl -s -X POST "${keycloak_url%/}/admin/realms" \
            -H "Authorization: Bearer $access_token" \
            -H "Content-Type: application/json" \
            -d "{\"realm\":\"$realm\",\"enabled\":true}"
    else
        echo "ℹ️  Realm $realm already exists"
    fi
    
    # Create frontend client (public)
    echo "🖥️  Creating frontend client: $frontend_client"
    curl -s -X POST "${keycloak_url%/}/admin/realms/$realm/clients" \
        -H "Authorization: Bearer $access_token" \
        -H "Content-Type: application/json" \
        -d "{
            \"clientId\":\"$frontend_client\",
            \"enabled\":true,
            \"publicClient\":true,
            \"directAccessGrantsEnabled\":true,
            \"standardFlowEnabled\":true,
            \"redirectUris\":[\"$frontend_url/*\"],
            \"webOrigins\":[\"$frontend_url\",\"$api_url\"]
        }" >/dev/null 2>&1
    
    # Create backend client (confidential)
    echo "🔧 Creating backend client: $backend_client"
    local backend_response
    backend_response=$(curl -s -X POST "${keycloak_url%/}/admin/realms/$realm/clients" \
        -H "Authorization: Bearer $access_token" \
        -H "Content-Type: application/json" \
        -d "{
            \"clientId\":\"$backend_client\",
            \"enabled\":true,
            \"publicClient\":false,
            \"serviceAccountsEnabled\":true,
            \"directAccessGrantsEnabled\":true,
            \"standardFlowEnabled\":false
        }")
    
    # Get backend client secret
    local clients_response
    clients_response=$(curl -s "${keycloak_url%/}/admin/realms/$realm/clients?clientId=$backend_client" \
        -H "Authorization: Bearer $access_token")
    
    local backend_id
    backend_id=$(python3 -c "import json,sys; data=json.load(sys.stdin); print(data[0]['id'] if data else '')" <<< "$clients_response" 2>/dev/null)
    
    local client_secret=""
    if [ -n "$backend_id" ]; then
        local secret_response
        secret_response=$(curl -s "${keycloak_url%/}/admin/realms/$realm/clients/$backend_id/client-secret" \
            -H "Authorization: Bearer $access_token")
        client_secret=$(python3 -c "import json,sys; print(json.load(sys.stdin).get('value',''))" <<< "$secret_response" 2>/dev/null)
    fi
    
    # Create roles
    echo "🏷️  Creating roles..."
    for role in "statechecker:admin" "statechecker:read"; do
        curl -s -X POST "${keycloak_url%/}/admin/realms/$realm/roles" \
            -H "Authorization: Bearer $access_token" \
            -H "Content-Type: application/json" \
            -d "{\"name\":\"$role\"}" >/dev/null 2>&1
    done
    
    # Create admin user if requested
    if [ -n "$admin_username" ]; then
        echo "👤 Creating user: $admin_username"
        curl -s -X POST "${keycloak_url%/}/admin/realms/$realm/users" \
            -H "Authorization: Bearer $access_token" \
            -H "Content-Type: application/json" \
            -d "{
                \"username\":\"$admin_username\",
                \"email\":\"$admin_email\",
                \"enabled\":true,
                \"emailVerified\":true,
                \"credentials\":[{\"type\":\"password\",\"value\":\"$admin_userpass\",\"temporary\":false}]
            }" >/dev/null 2>&1
        
        # Get user ID and assign role
        local users_response
        users_response=$(curl -s "${keycloak_url%/}/admin/realms/$realm/users?username=$admin_username" \
            -H "Authorization: Bearer $access_token")
        
        local user_id
        user_id=$(python3 -c "import json,sys; data=json.load(sys.stdin); print(data[0]['id'] if data else '')" <<< "$users_response" 2>/dev/null)
        
        if [ -n "$user_id" ]; then
            # Get role ID
            local role_response
            role_response=$(curl -s "${keycloak_url%/}/admin/realms/$realm/roles/statechecker:admin" \
                -H "Authorization: Bearer $access_token")
            
            local role_id role_name
            role_id=$(python3 -c "import json,sys; print(json.load(sys.stdin).get('id',''))" <<< "$role_response" 2>/dev/null)
            role_name=$(python3 -c "import json,sys; print(json.load(sys.stdin).get('name',''))" <<< "$role_response" 2>/dev/null)
            
            if [ -n "$role_id" ]; then
                curl -s -X POST "${keycloak_url%/}/admin/realms/$realm/users/$user_id/role-mappings/realm" \
                    -H "Authorization: Bearer $access_token" \
                    -H "Content-Type: application/json" \
                    -d "[{\"id\":\"$role_id\",\"name\":\"$role_name\"}]" >/dev/null 2>&1
                echo "✅ Assigned statechecker:admin role to $admin_username"
            fi
        fi
    fi
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "✅ Bootstrap complete!"
    echo ""
    echo "📋 Update your .env with these values:"
    echo ""
    echo "   KEYCLOAK_ENABLED=true"
    echo "   KEYCLOAK_URL=$keycloak_url"
    echo "   KEYCLOAK_REALM=$realm"
    echo "   KEYCLOAK_CLIENT_ID=$frontend_client"
    echo "   KEYCLOAK_BACKEND_CLIENT_ID=$backend_client"
    if [ -n "$client_secret" ]; then
        echo "   KEYCLOAK_CLIENT_SECRET=$client_secret"
    fi
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    
    return 0
}
