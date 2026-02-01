/**
 * Statechecker Admin UI
 *
 * Main application JavaScript for managing state checks through the API.
 * This file handles tab loading, Keycloak authentication, and global UI functionality.
 * 
 * NOTE: Token authentication has been removed. Keycloak SSO is required.
 * API token authentication is available for API-only access, not the web UI.
 */

// DOM Elements
const loginSection = document.getElementById('login-section');
const mainSection = document.getElementById('main-section');
const loginBtn = document.getElementById('loginBtn');
const loginError = document.getElementById('login-error');
const loginSession = document.getElementById('login-session');
const loginSessionName = document.getElementById('login-session-name');
const logoutBtn = document.getElementById('logoutBtn');
const userBadge = document.getElementById('userBadge');
const userName = document.getElementById('userName');
const statusMessage = document.getElementById('status-message');
const statusMessageBottom = document.getElementById('status-message-bottom');
const tabContentContainer = document.getElementById('tab-content-container');

// Track loaded scripts to avoid duplicate loading
const loadedScripts = new Set();

/** Track the Keycloak user for display purposes. */
let cachedKeycloakUser = null;

/**
 * Build a friendly label for a Keycloak user.
 *
 * @param {Object|null} user - Keycloak user payload.
 * @returns {string} Display label.
 */
function getUserDisplayName(user) {
    if (!user) return 'Unknown user';
    return user.name || user.username || user.email || 'Unknown user';
}

/**
 * Update the header badge with the current user.
 *
 * @param {Object|null} user - Keycloak user payload.
 */
function updateUserBadge(user) {
    cachedKeycloakUser = user || null;
    if (!userBadge || !userName) return;

    if (!user) {
        userBadge.classList.add('hidden');
        userName.textContent = '';
        return;
    }

    userName.textContent = getUserDisplayName(user);
    userBadge.classList.remove('hidden');
}

/**
 * Update the login screen when a session is already present.
 *
 * @param {Object|null} user - Keycloak user payload.
 */
function updateLoginSessionInfo(user) {
    if (!loginSession || !loginSessionName || !loginBtn) return;

    if (!user) {
        loginSession.classList.add('hidden');
        loginSessionName.textContent = '';
        loginBtn.textContent = 'Login with Keycloak';
        return;
    }

    loginSessionName.textContent = getUserDisplayName(user);
    loginSession.classList.remove('hidden');
    loginBtn.textContent = `Continue as ${getUserDisplayName(user)}`;
}

/**
 * Trim a value to remove whitespace.
 *
 * @param {any} value Input value.
 * @returns {string} Trimmed string.
 */
function trimValue(value) {
    if (value === null || value === undefined) return '';
    return String(value).trim();
}
window.trimValue = trimValue;

/**
 * Determine whether Keycloak authentication is enabled.
 * Keycloak is now REQUIRED for UI access.
 *
 * @returns {boolean} True when Keycloak is enabled.
 */
function isKeycloakFeatureEnabled() {
    return window.KEYCLOAK_ENABLED === true || window.KEYCLOAK_ENABLED === 'true';
}

/**
 * Build headers for admin API calls.
 * Uses Keycloak JWT token for authentication.
 *
 * @returns {Promise<Record<string, string>>} Headers.
 */
async function buildAuthHeaders() {
    const baseHeaders = {
        'Content-Type': 'application/json',
    };

    if (typeof getKeycloakToken !== 'function') {
        throw new Error('Keycloak authentication is not available. Please configure Keycloak.');
    }
    
    const token = await getKeycloakToken();
    if (!token) {
        throw new Error('Not authenticated. Please login with Keycloak.');
    }
    
    return {
        ...baseHeaders,
        Authorization: `Bearer ${token}`,
    };
}

/**
 * Make an API call with authentication.
 *
 * @param {string} endpoint - API endpoint path.
 * @param {string} [method='GET'] - HTTP method.
 * @param {Object} [body] - Request body for POST/PUT/DELETE.
 * @returns {Promise<any>} Parsed JSON response.
 */
async function apiCall(endpoint, method = 'GET', body = null) {
    const headers = await buildAuthHeaders();
    const options = { method, headers };

    if (body && (method === 'POST' || method === 'PUT' || method === 'DELETE')) {
        options.body = JSON.stringify(body);
    }

    const response = await fetch(endpoint, options);

    if (!response.ok) {
        const text = await response.text().catch(() => '');
        throw new Error(`${response.status} ${response.statusText}${text ? ` - ${text}` : ''}`);
    }

    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
        return response.json();
    }
    return response.text();
}

/**
 * Make an API call with authentication, but handle auth errors gracefully.
 *
 * @param {string} endpoint - API endpoint path.
 * @param {string} [method='GET'] - HTTP method.
 * @param {Object} [body] - Request body for POST/PUT/DELETE.
 * @returns {Promise<any|null>} Parsed JSON response or null if not authenticated.
 */
async function apiCallWithAuthCheck(endpoint, method = 'GET', body = null) {
    try {
        return await apiCall(endpoint, method, body);
    } catch (error) {
        // If it's an authentication error, return null instead of throwing
        if (error.message && error.message.includes('Not authenticated')) {
            return null;
        }
        // For other errors, still throw
        throw error;
    }
}
window.apiCall = apiCall;
window.apiCallWithAuthCheck = apiCallWithAuthCheck;

// UI Functions
/**
 * Set status message content and visibility.
 *
 * @param {HTMLElement} el - Status element.
 * @param {string} message - Status message.
 * @param {string} type - Status type (success|info|warning|error).
 * @param {boolean} persist - When true, do not auto-hide.
 */
function setStatusMessage(el, message, type, persist) {
    if (!el) return;
    if (el._hideTimeout) {
        clearTimeout(el._hideTimeout);
        el._hideTimeout = null;
    }
    const textEl = el.querySelector('.status-text');
    const closeEl = el.querySelector('.status-close');
    if (textEl) {
        textEl.textContent = message;
    } else {
        el.textContent = message;
    }

    el.className = `status ${type}`;
    el.classList.remove('hidden');

    if (closeEl) {
        closeEl.onclick = () => {
            clearStatusMessages(true);
        };
    }

    if (!persist) {
        el._hideTimeout = setTimeout(() => {
            el.classList.add('hidden');
            el._hideTimeout = null;
        }, 3500);
    }
}

/**
 * Show a status message.
 *
 * @param {string} message - Status message.
 * @param {string} [type='success'] - Status type.
 * @param {boolean|null} [persist=null] - Persist flag.
 */
function showStatus(message, type = 'success', persist = null) {
    const shouldPersist = persist === null ? (type === 'error' || type === 'warning') : Boolean(persist);
    setStatusMessage(statusMessage, message, type, shouldPersist);
    setStatusMessage(statusMessageBottom, message, type, shouldPersist);
}
window.showStatus = showStatus;

/**
 * Hide global status messages.
 *
 * @param {boolean} force - When true, also hides error/warning banners.
 */
function clearStatusMessages(force = false) {
    const shouldPreserve = (el) => {
        if (!el) return false;
        if (force) return false;
        return el.classList.contains('error') || el.classList.contains('warning');
    };

    if (statusMessage && !shouldPreserve(statusMessage)) statusMessage.classList.add('hidden');
    if (statusMessageBottom && !shouldPreserve(statusMessageBottom)) statusMessageBottom.classList.add('hidden');
}
window.clearStatusMessages = clearStatusMessages;

/**
 * Show the login section and hide main content.
 */
function showLogin() {
    if (loginSection) loginSection.classList.remove('hidden');
    if (mainSection) mainSection.classList.add('hidden');
    if (logoutBtn) logoutBtn.classList.add('hidden');
    updateUserBadge(null);
    updateLoginSessionInfo(cachedKeycloakUser);
}

/**
 * Show the main application section.
 */
function showMain() {
    if (loginSection) loginSection.classList.add('hidden');
    if (mainSection) mainSection.classList.remove('hidden');
    if (logoutBtn) logoutBtn.classList.remove('hidden');
    updateUserBadge(cachedKeycloakUser);
    updateLoginSessionInfo(null);
}

/**
 * Set login error message.
 *
 * @param {string} message - Error message.
 */
function setLoginError(message) {
    if (!loginError) return;
    loginError.textContent = message;
    loginError.classList.remove('hidden');
}

/**
 * Clear login error message.
 */
function clearLoginError() {
    if (!loginError) return;
    loginError.textContent = '';
    loginError.classList.add('hidden');
}

// Tab Navigation and Loading
/**
 * Load tab content (HTML + JS) dynamically.
 *
 * @param {string} tabName - Tab name (tools, websites, backups, gdrive).
 * @returns {Promise<void>}
 */
async function loadTabContent(tabName) {
    try {
        const response = await fetch(`./${tabName}/${tabName}.html`);
        if (!response.ok) {
            throw new Error(`Failed to load ${tabName} tab`);
        }
        const html = await response.text();
        tabContentContainer.innerHTML = html;

        const tabRoot = tabContentContainer.querySelector('.tab-content');
        if (tabRoot) {
            tabRoot.classList.add('active');
            tabRoot.classList.remove('hidden');
        }

        // Check if script already loaded
        if (loadedScripts.has(tabName)) {
            initializeTab(tabName);
            return;
        }

        // Load and initialize tab-specific JavaScript
        const script = document.createElement('script');
        script.src = `./${tabName}/${tabName}.js`;
        script.onload = () => {
            loadedScripts.add(tabName);
            initializeTab(tabName);
        };
        script.onerror = () => {
            console.error(`Failed to load script for tab ${tabName}`);
            tabContentContainer.innerHTML += `<div class="status error">Error loading ${tabName} functionality.</div>`;
        };
        document.head.appendChild(script);

    } catch (error) {
        console.error(`Failed to load tab ${tabName}:`, error);
        tabContentContainer.innerHTML = `<div class="card"><p class="error">Error loading ${tabName} tab content.</p></div>`;
    }
}

/**
 * Initialize a tab after its script has loaded.
 *
 * @param {string} tabName - Tab name.
 */
function initializeTab(tabName) {
    switch (tabName) {
        case 'tools':
            if (typeof initToolsTab === 'function') initToolsTab();
            break;
        case 'websites':
            if (typeof initWebsitesTab === 'function') initWebsitesTab();
            break;
        case 'backups':
            if (typeof initBackupsTab === 'function') initBackupsTab();
            break;
        case 'gdrive':
            if (typeof initGdriveTab === 'function') initGdriveTab();
            break;
    }

    loadTabData(tabName);
}

/**
 * Load data for a specific tab.
 *
 * @param {string} tabName - Tab name.
 * @returns {Promise<void>}
 */
async function loadTabData(tabName) {
    try {
        switch (tabName) {
            case 'tools':
                if (typeof loadTools === 'function') await loadTools();
                break;
            case 'websites':
                if (typeof loadWebsites === 'function') await loadWebsites();
                break;
            case 'backups':
                if (typeof loadBackups === 'function') await loadBackups();
                break;
            case 'gdrive':
                if (typeof loadGdriveFolders === 'function') await loadGdriveFolders();
                break;
        }
    } catch (error) {
        showStatus(`Failed to load ${tabName} data: ${error.message}`, 'error');
    }
}

/**
 * Switch to a tab.
 *
 * @param {string} tabName - Tab name.
 * @returns {Promise<void>}
 */
async function switchTab(tabName) {
    // Update tab button states
    document.querySelectorAll('.tabs .tab').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    await loadTabContent(tabName);
}

// Version Display
/**
 * Fetch and display API version.
 */
async function fetchApiVersion() {
    try {
        const response = await fetch('/version');
        if (response.ok) {
            const data = await response.json();
            document.getElementById('apiVersion').textContent = data.version || 'unknown';
        } else {
            document.getElementById('apiVersion').textContent = 'unavailable';
        }
    } catch (e) {
        document.getElementById('apiVersion').textContent = 'unavailable';
    }
}

/**
 * Fetch and display web version.
 *
 * Tries multiple paths to support both nginx (web service) and API (/admin) access.
 */
async function fetchWebVersion() {
    const setVersion = (rawVersion) => {
        const version = trimValue(rawVersion) || 'local';
        document.getElementById('webVersion').textContent = version;
        window.APP_VERSION = version;
        window.APP_IS_DEV = version.toLowerCase() === 'dev' || version.toLowerCase().includes('local');
    };

    // Try relative path first (works for /admin mount)
    try {
        const response = await fetch('./web-version.json', { cache: 'no-store' });
        if (response.ok) {
            const data = await response.json();
            setVersion(data.version);
            return;
        }
    } catch { /* continue to next fallback */ }

    // Try absolute path (works for nginx web service)
    try {
        const response = await fetch('/web-version.json', { cache: 'no-store' });
        if (response.ok) {
            const data = await response.json();
            setVersion(data.version);
            return;
        }
    } catch { /* continue to next fallback */ }

    // Fall back to API version endpoint
    try {
        const response = await fetch('/version', { cache: 'no-store' });
        if (response.ok) {
            const data = await response.json();
            setVersion(data.version);
            return;
        }
    } catch { /* use default */ }

    setVersion('local');
}

// Authentication Handlers
/**
 * Handle Keycloak login button click.
 */
async function handleLogin() {
    clearLoginError();
    if (typeof keycloakLogin !== 'function') {
        setLoginError('Keycloak is not available. Check configuration.');
        return;
    }

    if (typeof isKeycloakAuthenticated === 'function' && isKeycloakAuthenticated()) {
        cachedKeycloakUser = typeof getKeycloakUser === 'function' ? getKeycloakUser() : cachedKeycloakUser;
        updateUserBadge(cachedKeycloakUser);
        updateLoginSessionInfo(null);
        showMain();
        await switchTab('tools');
        return;
    }

    try {
        await keycloakLogin();
    } catch (error) {
        setLoginError(`Login failed: ${error.message || error}`);
    }
}

/**
 * Handle Keycloak logout.
 */
async function handleLogout() {
    if (typeof keycloakLogout === 'function') {
        try {
            await keycloakLogout();
        } catch (error) {
            showStatus(`Logout failed: ${error.message || error}`, 'error');
        }
    }
    cachedKeycloakUser = null;
    updateLoginSessionInfo(null);
    showLogin();
}

// Event Listeners Setup
/**
 * Setup all event listeners.
 */
function setupEventListeners() {
    // Login button
    if (loginBtn) {
        loginBtn.addEventListener('click', handleLogin);
    }

    // Logout button
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }

    // Tab navigation
    document.querySelectorAll('.tabs .tab').forEach(btn => {
        btn.addEventListener('click', () => {
            switchTab(btn.dataset.tab);
        });
    });
}

// Application Initialization
/**
 * Initialize the application.
 * Keycloak SSO is REQUIRED for UI access.
 */
async function init() {
    fetchApiVersion();
    fetchWebVersion();
    setupEventListeners();

    // Check if Keycloak is enabled
    if (!isKeycloakFeatureEnabled()) {
        showLogin();
        setLoginError('Keycloak is not enabled. Please configure KEYCLOAK_ENABLED=true in your environment and bootstrap the Keycloak realm.');
        showStatus('Keycloak SSO is required for UI access. Token authentication is only available for API calls.', 'error', true);
        return;
    }

    // Check if Keycloak adapter is loaded
    if (typeof initKeycloak !== 'function') {
        showLogin();
        setLoginError('Keycloak adapter failed to load. Check your Keycloak configuration.');
        showStatus('Keycloak authentication module is not available. Verify keycloak.js and keycloak-config.js are properly configured.', 'error', true);
        return;
    }

    if (typeof isKeycloakAdapterFallback === 'function' && isKeycloakAdapterFallback()) {
        showLogin();
        setLoginError('Keycloak adapter is unavailable. Allow Keycloak JS or rebuild the web image with the adapter.');
        return;
    }

    // Initialize Keycloak
    try {
        const authenticated = await initKeycloak();
        if (authenticated) {
            cachedKeycloakUser = typeof getKeycloakUser === 'function' ? getKeycloakUser() : null;
            updateUserBadge(cachedKeycloakUser);
            showMain();
            await switchTab('tools');
            return;
        }
    } catch (error) {
        setLoginError(`Keycloak initialization failed: ${error.message || error}`);
        showStatus(`Keycloak error: ${error.message || error}. Please verify your Keycloak server is running and the realm is properly configured.`, 'error', true);
    }

    showLogin();
}

// Start application
document.addEventListener('DOMContentLoaded', init);
