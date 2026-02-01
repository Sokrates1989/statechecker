/**
 * Google Drive Tab JavaScript
 *
 * Handles Google Drive folder monitoring configuration for the Statechecker Admin UI.
 */

/**
 * Load Google Drive folders from the API and refresh the UI.
 *
 * @returns {Promise<void>}
 */
async function loadGdriveFolders() {
    try {
        const data = await apiCallWithAuthCheck('/v1/admin/google-drive/folders');
        if (data === null) {
            // Not authenticated - clear data and show empty state
            window.gdriveFoldersData = [];
            renderGdriveFolders();
            return;
        }
        window.gdriveFoldersData = data.foldersToCheck || [];
        renderGdriveFolders();
    } catch (error) {
        showStatus(`Failed to load Google Drive folders: ${error.message}`, 'error');
    }
}

/**
 * Render the Google Drive folders list into the DOM.
 *
 * @returns {void}
 */
function renderGdriveFolders() {
    const container = document.getElementById('gdrive-list');
    const folders = window.gdriveFoldersData || [];

    if (folders.length === 0) {
        container.innerHTML = '<p class="no-items">No Google Drive folders configured. Add one above to get started.</p>';
        return;
    }

    container.innerHTML = `<pre class="mono">${escapeHtml(JSON.stringify(folders, null, 2))}</pre>`;
}

/**
 * Add or update a Google Drive folder configuration.
 *
 * @returns {Promise<void>}
 */
async function upsertGdriveFolder() {
    const jsonInput = document.getElementById('gdrive-folder-json');
    const raw = (jsonInput.value || '').trim();

    if (!raw) {
        showStatus('Please enter folder configuration JSON', 'error');
        return;
    }

    let folderConfig;
    try {
        folderConfig = JSON.parse(raw);
    } catch (e) {
        showStatus('Invalid JSON format', 'error');
        return;
    }

    if (!folderConfig.name) {
        showStatus('Folder configuration must include a "name" field', 'error');
        return;
    }

    try {
        await apiCall('/v1/admin/google-drive/folders', 'POST', folderConfig);
        showStatus(`Folder "${folderConfig.name}" saved`);
        jsonInput.value = '';
        await loadGdriveFolders();
    } catch (error) {
        showStatus(`Failed to save folder: ${error.message}`, 'error');
    }
}

/**
 * Remove a Google Drive folder by name.
 *
 * @returns {Promise<void>}
 */
async function removeGdriveFolder() {
    const nameInput = document.getElementById('gdrive-remove-name');
    const name = (nameInput.value || '').trim();

    if (!name) {
        showStatus('Please enter a folder name to remove', 'error');
        return;
    }

    if (!confirm(`Remove folder "${name}" from monitoring?`)) return;

    try {
        await apiCall('/v1/admin/google-drive/folders', 'DELETE', { name });
        showStatus(`Folder "${name}" removed`);
        nameInput.value = '';
        await loadGdriveFolders();
    } catch (error) {
        showStatus(`Failed to remove folder: ${error.message}`, 'error');
    }
}

/**
 * Escape HTML entities.
 *
 * @param {any} s - Input.
 * @returns {string} Escaped string.
 */
function escapeHtml(s) {
    return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

/**
 * Initialize event handlers for the Google Drive tab.
 *
 * @returns {void}
 */
function initGdriveTab() {
    const upsertBtn = document.getElementById('gdrive-upsert-btn');
    if (upsertBtn) {
        upsertBtn.addEventListener('click', upsertGdriveFolder);
    }

    const removeBtn = document.getElementById('gdrive-remove-btn');
    if (removeBtn) {
        removeBtn.addEventListener('click', removeGdriveFolder);
    }

    const refreshBtn = document.getElementById('gdrive-refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadGdriveFolders);
    }
}

// Expose for app.js
window.loadGdriveFolders = loadGdriveFolders;
window.renderGdriveFolders = renderGdriveFolders;
window.initGdriveTab = initGdriveTab;
