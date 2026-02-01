/**
 * Websites Tab JavaScript
 *
 * Handles website monitoring management for the Statechecker Admin UI.
 */

/**
 * Load websites from the API and refresh the UI.
 *
 * @returns {Promise<void>}
 */
async function loadWebsites() {
    try {
        const data = await apiCallWithAuthCheck('/v1/admin/websites');
        if (data === null) {
            // Not authenticated - clear data and show empty state
            window.websitesData = [];
            renderWebsites();
            return;
        }
        window.websitesData = data.websites || [];
        renderWebsites();
    } catch (error) {
        showStatus(`Failed to load websites: ${error.message}`, 'error');
    }
}

/**
 * Render the websites list into the DOM.
 *
 * @returns {void}
 */
function renderWebsites() {
    const container = document.getElementById('websites-list');
    const websites = window.websitesData || [];

    if (websites.length === 0) {
        container.innerHTML = '<p class="no-items">No websites being watched. Add one above to get started.</p>';
        return;
    }

    container.innerHTML = websites.map(w => {
        const state = (w.state || '').toLowerCase();
        const statusClass = state === 'up' ? 'status-up' : state === 'down' ? 'status-down' : 'status-unknown';
        const statusLabel = state === 'up' ? '🟢 Up' : state === 'down' ? '🔴 Down' : '❓ Unknown';
        const downMsgSent = w.isDownMessageHasBeenSent ? '📨 Yes' : '—';

        return `
            <div class="item">
                <div class="item-header">
                    <h3 class="mono">${escapeHtml(w.url || '')}</h3>
                    <div class="item-actions">
                        <button class="btn btn-sm btn-danger" data-action="website-remove" data-url="${escapeHtml(w.url)}">Remove</button>
                    </div>
                </div>
                <div class="item-details">
                    <p><strong>Status:</strong> <span class="${statusClass}">${statusLabel}</span></p>
                    <p><strong>Down Notification Sent:</strong> ${downMsgSent}</p>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Normalize and validate a website URL.
 *
 * @param {string} input - User input URL.
 * @returns {string[]} Array of URLs to add (http and/or https variants).
 */
function normalizeWebsiteUrl(input) {
    input = input.trim();
    if (!input) return [];

    if (/^https?:\/\//i.test(input)) {
        return [input];
    }

    input = input.replace(/^[a-z]+:\/*/i, '');

    const domainPattern = /^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+(\/.*)?$/i;
    if (!domainPattern.test(input)) {
        return [];
    }

    return [`http://${input}`, `https://${input}`];
}

/**
 * Add a new website from the input field.
 *
 * @returns {Promise<void>}
 */
async function addWebsite() {
    const input = document.getElementById('website-url-input');
    const rawUrl = (input.value || '').trim();
    if (!rawUrl) return;

    const urls = normalizeWebsiteUrl(rawUrl);
    if (urls.length === 0) {
        showStatus('Invalid URL. Please enter a valid domain or full URL.', 'error');
        return;
    }

    try {
        for (const url of urls) {
            await apiCall('/v1/admin/websites', 'POST', { url });
        }
        input.value = '';
        showStatus(`Website(s) added: ${urls.join(', ')}`);
        await loadWebsites();
    } catch (error) {
        showStatus(`Failed to add website: ${error.message}`, 'error');
    }
}

/**
 * Remove a website by URL.
 *
 * @param {string} url - Website URL.
 * @returns {Promise<void>}
 */
async function removeWebsite(url) {
    if (!confirm(`Remove website "${url}" from monitoring?`)) return;

    try {
        await apiCall('/v1/admin/websites', 'DELETE', { url });
        showStatus(`Website "${url}" removed`);
        await loadWebsites();
    } catch (error) {
        showStatus(`Failed to remove website: ${error.message}`, 'error');
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
 * Initialize event handlers for the websites tab.
 *
 * @returns {void}
 */
function initWebsitesTab() {
    const addBtn = document.getElementById('website-add-btn');
    if (addBtn) {
        addBtn.addEventListener('click', addWebsite);
    }

    const urlInput = document.getElementById('website-url-input');
    if (urlInput) {
        urlInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                addWebsite();
            }
        });
    }

    const refreshBtn = document.getElementById('websites-refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadWebsites);
    }

    const list = document.getElementById('websites-list');
    if (list) {
        list.addEventListener('click', (e) => {
            const btn = e.target.closest('button[data-action]');
            if (!btn) return;
            const action = btn.getAttribute('data-action');
            const url = btn.getAttribute('data-url');
            if (!url) return;

            if (action === 'website-remove') {
                removeWebsite(url);
            }
        });
    }
}

// Expose for app.js
window.loadWebsites = loadWebsites;
window.renderWebsites = renderWebsites;
window.initWebsitesTab = initWebsitesTab;
