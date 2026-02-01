/**
 * Backups Tab JavaScript
 *
 * Handles backup monitoring management for the Statechecker Admin UI.
 */

/**
 * Load backups from the API and refresh the UI.
 *
 * @returns {Promise<void>}
 */
async function loadBackups() {
    try {
        const data = await apiCallWithAuthCheck('/v1/admin/backups');
        if (data === null) {
            // Not authenticated - clear data and show empty state
            window.backupsData = [];
            renderBackups();
            return;
        }
        window.backupsData = data.backups || [];
        renderBackups();
    } catch (error) {
        showStatus(`Failed to load backups: ${error.message}`, 'error');
    }
}

/**
 * Format a unix timestamp (seconds) to locale date string with relative age.
 *
 * @param {string|number|null|undefined} ts - Unix timestamp in seconds.
 * @returns {string} Formatted string.
 */
function formatBackupTimestamp(ts) {
    if (!ts) return '-';
    const num = parseInt(ts, 10);
    if (isNaN(num) || num <= 0) return String(ts);
    const d = new Date(num * 1000);

    const nowSeconds = Math.floor(Date.now() / 1000);
    const diff = Math.max(0, nowSeconds - num);
    const minute = 60;
    const hour = 60 * minute;
    const day = 24 * hour;

    let age;
    if (diff < minute) age = 'just now';
    else if (diff < hour) age = `${Math.floor(diff / minute)}m ago`;
    else if (diff < day) age = `${Math.floor(diff / hour)}h ago`;
    else age = `${Math.floor(diff / day)}d ago`;

    return `${d.toLocaleString()} (${age})`;
}

/**
 * Render the backups list into the DOM.
 *
 * @returns {void}
 */
function renderBackups() {
    const container = document.getElementById('backups-list');
    const backups = window.backupsData || [];

    if (backups.length === 0) {
        container.innerHTML = '<p class="no-items">No backups being watched. Backups appear here when clients send /v1/backupcheck pings.</p>';
        return;
    }

    container.innerHTML = backups.map(b => {
        const freqOverride = b.frequencyOverride_inMinutes != null
            ? `<span class="badge warn">${b.frequencyOverride_inMinutes}m override</span>`
            : '';

        return `
            <div class="item">
                <div class="item-header">
                    <h3>${escapeHtml(b.name || 'Unnamed')}</h3>
                    <div class="item-actions">
                        <button class="btn btn-sm btn-secondary" data-action="backup-freq" data-name="${escapeHtml(b.name)}">Set Freq</button>
                        <button class="btn btn-sm btn-danger" data-action="backup-unwatch" data-name="${escapeHtml(b.name)}">Unwatch</button>
                    </div>
                </div>
                <div class="item-details">
                    <p><strong>Frequency:</strong> ${b.stateCheckFrequency_inMinutes ?? '-'}m ${freqOverride}</p>
                    <p><strong>Most Recent Backup:</strong> ${formatBackupTimestamp(b.mostRecentBackupFile_creationDate)}</p>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Unwatch (delete) a backup by name.
 *
 * @param {string} name - Backup name.
 * @returns {Promise<void>}
 */
async function unwatchBackup(name) {
    if (!confirm(`Unwatch backup "${name}"? It will reappear if the client sends pings again.`)) return;

    try {
        await apiCall('/v1/admin/backups', 'DELETE', { name });
        showStatus(`Backup "${name}" unwatched`);
        await loadBackups();
    } catch (error) {
        showStatus(`Failed to unwatch backup: ${error.message}`, 'error');
    }
}

/**
 * Show the frequency modal for a backup.
 *
 * @param {string} name - Backup name.
 * @returns {void}
 */
function showBackupFrequencyModal(name) {
    const modal = document.getElementById('backup-frequency-modal');
    document.getElementById('backup-frequency-target-name').value = name;
    document.getElementById('backup-frequency-input').value = '';
    document.getElementById('backup-frequency-modal-title').textContent = `Set Frequency: ${name}`;
    modal.classList.remove('hidden');
}

/**
 * Hide the frequency modal.
 *
 * @returns {void}
 */
function hideBackupFrequencyModal() {
    document.getElementById('backup-frequency-modal').classList.add('hidden');
}

/**
 * Parse duration input to minutes.
 *
 * @param {string} input - User input.
 * @returns {number|null} Minutes or null.
 */
function parseFrequencyInput(input) {
    if (!input) return null;
    input = input.trim().toLowerCase();
    let match = input.match(/^([\d.]+)\s*(m|min|mins|minutes?)?$/);
    if (match) return Math.round(parseFloat(match[1]));
    match = input.match(/^([\d.]+)\s*(h|hr|hrs|hours?)$/);
    if (match) return Math.round(parseFloat(match[1]) * 60);
    match = input.match(/^([\d.]+)\s*(d|days?)$/);
    if (match) return Math.round(parseFloat(match[1]) * 60 * 24);
    const num = parseFloat(input);
    if (!isNaN(num)) return Math.round(num);
    return null;
}

/**
 * Save the frequency override from the modal.
 *
 * @returns {Promise<void>}
 */
async function saveBackupFrequency() {
    const name = document.getElementById('backup-frequency-target-name').value;
    const input = document.getElementById('backup-frequency-input').value;
    const minutes = parseFrequencyInput(input);

    if (!minutes || minutes <= 0) {
        showStatus('Invalid frequency. Use formats like: 60, 2h, 1d', 'error');
        return;
    }

    try {
        await apiCall('/v1/admin/backups/frequency', 'POST', {
            name,
            stateCheckFrequency_inMinutes: minutes
        });
        showStatus(`Frequency updated for "${name}"`);
        hideBackupFrequencyModal();
        await loadBackups();
    } catch (error) {
        showStatus(`Failed to set frequency: ${error.message}`, 'error');
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
 * Initialize event handlers for the backups tab.
 *
 * @returns {void}
 */
function initBackupsTab() {
    const refreshBtn = document.getElementById('backups-refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadBackups);
    }

    const list = document.getElementById('backups-list');
    if (list) {
        list.addEventListener('click', (e) => {
            const btn = e.target.closest('button[data-action]');
            if (!btn) return;
            const action = btn.getAttribute('data-action');
            const name = btn.getAttribute('data-name');
            if (!name) return;

            if (action === 'backup-unwatch') {
                unwatchBackup(name);
            } else if (action === 'backup-freq') {
                showBackupFrequencyModal(name);
            }
        });
    }

    const modal = document.getElementById('backup-frequency-modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target.id === 'backup-frequency-modal') {
                hideBackupFrequencyModal();
            }
        });
        modal.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', hideBackupFrequencyModal);
        });
    }

    const saveBtn = document.getElementById('backup-frequency-save-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', saveBackupFrequency);
    }
}

// Expose for app.js
window.loadBackups = loadBackups;
window.renderBackups = renderBackups;
window.initBackupsTab = initBackupsTab;
