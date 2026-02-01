/**
 * Tools Tab JavaScript
 *
 * Handles tool monitoring management for the Statechecker Admin UI.
 */

/**
 * Load tools from the API and refresh the UI.
 *
 * @returns {Promise<void>}
 */
async function loadTools() {
    try {
        const data = await apiCallWithAuthCheck('/v1/admin/tools');
        if (data === null) {
            // Not authenticated - clear data and show empty state
            window.toolsData = [];
            renderTools();
            return;
        }
        window.toolsData = data.tools || [];
        renderTools();
    } catch (error) {
        showStatus(`Failed to load tools: ${error.message}`, 'error');
    }
}

/**
 * Determine if a tool is up based on last-up timestamp and expected frequency.
 *
 * @param {Object} t - Tool row object.
 * @returns {boolean|null} True/False if computable, else null.
 */
function isToolUp(t) {
    if (!t.lastTimeToolWasUp || !t.stateCheckFrequency_inMinutes) return null;
    const lastUp = parseInt(t.lastTimeToolWasUp, 10);
    if (isNaN(lastUp)) return null;
    const freq = t.frequencyOverride_inMinutes ?? t.stateCheckFrequency_inMinutes;
    const now = Math.floor(Date.now() / 1000);
    const threshold = freq * 60 * 1.5;
    return (now - lastUp) <= threshold;
}

/**
 * Format a unix timestamp (seconds) to locale date string with relative age.
 *
 * @param {string|number|null|undefined} ts - Unix timestamp in seconds.
 * @returns {string} Formatted string.
 */
function formatToolTimestamp(ts) {
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
 * Render the tools list into the DOM.
 *
 * @returns {void}
 */
function renderTools() {
    const container = document.getElementById('tools-list');
    const tools = window.toolsData || [];

    if (tools.length === 0) {
        container.innerHTML = '<p class="no-items">No tools being watched. Tools appear here when clients send /v1/statecheck pings.</p>';
        return;
    }

    container.innerHTML = tools.map(t => {
        const upStatus = isToolUp(t);
        const statusClass = upStatus === true ? 'status-up' : upStatus === false ? 'status-down' : 'status-unknown';
        const statusLabel = upStatus === true ? '🟢 Up' : upStatus === false ? '🔴 Down' : '❓ Unknown';
        const freqOverride = t.frequencyOverride_inMinutes != null
            ? `<span class="badge warn">${t.frequencyOverride_inMinutes}m override</span>`
            : '';

        return `
            <div class="item">
                <div class="item-header">
                    <h3>${escapeHtml(t.name || 'Unnamed')}</h3>
                    <div class="item-actions">
                        <button class="btn btn-sm btn-secondary" data-action="tool-freq" data-name="${escapeHtml(t.name)}">Set Freq</button>
                        <button class="btn btn-sm btn-danger" data-action="tool-unwatch" data-name="${escapeHtml(t.name)}">Unwatch</button>
                    </div>
                </div>
                <div class="item-details">
                    <p><strong>Status:</strong> <span class="${statusClass}">${statusLabel}</span></p>
                    <p><strong>Frequency:</strong> ${t.stateCheckFrequency_inMinutes ?? '-'}m ${freqOverride}</p>
                    <p><strong>Last Up:</strong> ${formatToolTimestamp(t.lastTimeToolWasUp)}</p>
                    ${t.description ? `<p><strong>Description:</strong> ${escapeHtml(t.description)}</p>` : ''}
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Unwatch (delete) a tool by name.
 *
 * @param {string} name - Tool name.
 * @returns {Promise<void>}
 */
async function unwatchTool(name) {
    if (!confirm(`Unwatch tool "${name}"? It will reappear if the client sends pings again.`)) return;

    try {
        await apiCall('/v1/admin/tools', 'DELETE', { name });
        showStatus(`Tool "${name}" unwatched`);
        await loadTools();
    } catch (error) {
        showStatus(`Failed to unwatch tool: ${error.message}`, 'error');
    }
}

/**
 * Show the frequency modal for a tool.
 *
 * @param {string} name - Tool name.
 * @returns {void}
 */
function showToolFrequencyModal(name) {
    const modal = document.getElementById('tool-frequency-modal');
    document.getElementById('tool-frequency-target-name').value = name;
    document.getElementById('tool-frequency-input').value = '';
    document.getElementById('tool-frequency-modal-title').textContent = `Set Frequency: ${name}`;
    modal.classList.remove('hidden');
}

/**
 * Hide the frequency modal.
 *
 * @returns {void}
 */
function hideToolFrequencyModal() {
    document.getElementById('tool-frequency-modal').classList.add('hidden');
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
async function saveToolFrequency() {
    const name = document.getElementById('tool-frequency-target-name').value;
    const input = document.getElementById('tool-frequency-input').value;
    const minutes = parseFrequencyInput(input);

    if (!minutes || minutes <= 0) {
        showStatus('Invalid frequency. Use formats like: 5, 30m, 2h, 1d', 'error');
        return;
    }

    try {
        await apiCall('/v1/admin/tools/frequency', 'POST', {
            name,
            stateCheckFrequency_inMinutes: minutes
        });
        showStatus(`Frequency updated for "${name}"`);
        hideToolFrequencyModal();
        await loadTools();
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
 * Initialize event handlers for the tools tab.
 *
 * @returns {void}
 */
function initToolsTab() {
    const refreshBtn = document.getElementById('tools-refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadTools);
    }

    const list = document.getElementById('tools-list');
    if (list) {
        list.addEventListener('click', (e) => {
            const btn = e.target.closest('button[data-action]');
            if (!btn) return;
            const action = btn.getAttribute('data-action');
            const name = btn.getAttribute('data-name');
            if (!name) return;

            if (action === 'tool-unwatch') {
                unwatchTool(name);
            } else if (action === 'tool-freq') {
                showToolFrequencyModal(name);
            }
        });
    }

    const modal = document.getElementById('tool-frequency-modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target.id === 'tool-frequency-modal') {
                hideToolFrequencyModal();
            }
        });
        modal.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', hideToolFrequencyModal);
        });
    }

    const saveBtn = document.getElementById('tool-frequency-save-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', saveToolFrequency);
    }
}

// Expose for app.js
window.loadTools = loadTools;
window.renderTools = renderTools;
window.initToolsTab = initToolsTab;
