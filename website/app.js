/* app.js */

/**
 * Get a DOM element by id.
 *
 * @param {string} id - Element id.
 * @returns {HTMLElement} Element.
 */
const $ = (id) => document.getElementById(id);

/** Track last refresh timestamp. */
let lastRefreshTime = null;

/** Auto-refresh interval ID. */
let autoRefreshInterval = null;

/** Time ago update interval ID. */
let timeAgoInterval = null;

/** Auto-refresh interval in milliseconds. */
const AUTO_REFRESH_INTERVAL_MS = 60000;

/**
 * Resolve API base URL from settings.
 *
 * @returns {string} Base URL without trailing slash (always empty for relative paths).
 */
function getApiBase() {
  return '';
}

/**
 * Resolve server auth token from settings.
 *
 * @returns {string} Token.
 */
function getToken() {
  return ($('token').value || '').trim();
}

/**
 * Build headers for admin API calls.
 *
 * @returns {Record<string, string>} Headers.
 */
function headers() {
  const token = getToken();
  return {
    'Content-Type': 'application/json',
    'X-Server-Authentication-Token': token,
  };
}

/**
 * Fetch helper for the admin API.
 *
 * @param {string} path - API path (e.g. /v1/admin/tools).
 * @param {object} [options] - Fetch options.
 * @returns {Promise<any>} Parsed JSON or text.
 */
async function apiFetch(path, options = {}) {
  const base = getApiBase();
  const url = base ? base + path : path;
  const res = await fetch(url, {
    ...options,
    headers: { ...(options.headers || {}), ...headers() },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`${res.status} ${res.statusText}${text ? ` - ${text}` : ''}`);
  }
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) return res.json();
  return res.text();
}

/**
 * Update status label.
 *
 * @param {string} msg - Message.
 */
function setStatus(msg) {
  $('status').textContent = msg;
}

/**
 * Load settings from session storage.
 */
function loadSettings() {
  $('token').value = sessionStorage.getItem('statechecker_admin_token') || '';
}

/**
 * Save settings to session storage and validate token by refreshing all data.
 */
async function saveSettings() {
  sessionStorage.setItem('statechecker_admin_token', $('token').value || '');
  setStatus('Validating token...');
  try {
    await refreshAll();
    setStatus('Token saved, validated and refreshed states.');
  } catch (e) {
    setStatus('Token saved but validation failed: ' + String(e));
  }
}

/**
 * Switch the active tab.
 *
 * @param {string} tab - Tab id.
 */
function setActiveTab(tab) {
  for (const btn of document.querySelectorAll('#tabs .tab')) {
    btn.classList.toggle('active', btn.dataset.tab === tab);
  }
  for (const id of ['tools', 'websites', 'backups', 'gdrive']) {
    const panel = $('panel-' + id);
    if (panel) panel.style.display = (id === tab) ? 'block' : 'none';
  }
}

/**
 * Format age string from a unix timestamp.
 *
 * @param {number} tsSeconds - Unix timestamp in seconds.
 * @returns {string} Human readable age (e.g., "> 2 years ago").
 */
function formatAgeFromTimestampSeconds(tsSeconds) {
  const nowSeconds = Math.floor(Date.now() / 1000);
  const diff = Math.max(0, nowSeconds - tsSeconds);

  const minute = 60;
  const hour = 60 * minute;
  const day = 24 * hour;
  const month = 30 * day;
  const year = 365 * day;

  if (diff < minute) return 'just now';
  if (diff < hour) return `${Math.floor(diff / minute)} minutes ago`;
  if (diff < day) return `${Math.floor(diff / hour)} hours ago`;
  if (diff < month) return `${Math.floor(diff / day)} days ago`;
  if (diff < year) return `${Math.floor(diff / month)} months ago`;
  return `${Math.floor(diff / year)} years ago`;
}

/**
 * Format a unix timestamp (seconds) to locale date string with relative age.
 *
 * @param {string|number|null|undefined} ts - Unix timestamp in seconds.
 * @returns {string} Formatted string.
 */
function formatTimestamp(ts) {
  if (!ts) return '-';
  const num = parseInt(ts, 10);
  if (isNaN(num) || num <= 0) return String(ts);
  const d = new Date(num * 1000);
  const age = formatAgeFromTimestampSeconds(num);
  return `${d.toLocaleString()} (${age})`;
}

/**
 * Determine if a tool is up based on last-up timestamp and expected frequency.
 *
 * @param {any} t - Tool row object.
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
 * Prompt for a frequency change and apply it via admin API.
 *
 * @param {'tool'|'backup'} type - Target type.
 * @param {string} name - Target name.
 */
async function promptFrequencyChange(type, name) {
  const input = prompt(`Set check frequency for "${name}"\n\nEnter value (e.g. 5, 30m, 2h, 1d):`);
  if (!input) return;
  const minutes = parseFrequencyInput(input);
  if (!minutes || minutes <= 0) {
    alert('Invalid frequency. Use formats like: 5, 30m, 2h, 1d');
    return;
  }
  const endpoint = type === 'tool' ? '/v1/admin/tools/frequency' : '/v1/admin/backups/frequency';
  await apiFetch(endpoint, { method: 'POST', body: JSON.stringify({ name, stateCheckFrequency_inMinutes: minutes }) });
}

/**
 * Refresh all data from server.
 */
async function refreshAll() {
  await Promise.all([
    refreshTools(),
    refreshWebsites(),
    refreshBackups(),
    refreshGdrive()
  ]);
  updateLastRefreshTime();
}

/**
 * Update the last refresh timestamp display.
 */
function updateLastRefreshTime() {
  lastRefreshTime = new Date();
  updateTimeAgoDisplay();
}

/**
 * Update the time ago display.
 */
function updateTimeAgoDisplay() {
  const el = $('lastRefresh');
  if (!el || !lastRefreshTime) return;

  const now = new Date();
  const diffMs = now - lastRefreshTime;
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);

  let timeAgo;
  if (diffSecs < 5) {
    timeAgo = 'just now';
  } else if (diffSecs < 60) {
    timeAgo = `${diffSecs}s ago`;
  } else if (diffMins < 60) {
    timeAgo = `${diffMins}m ago`;
  } else {
    timeAgo = `${Math.floor(diffMins / 60)}h ago`;
  }

  el.textContent = `${lastRefreshTime.toLocaleTimeString()} (${timeAgo})`;
}

/**
 * Refresh tools table.
 */
async function refreshTools() {
  const data = await apiFetch('/v1/admin/tools');
  const body = $('toolsBody');
  body.innerHTML = '';
  for (const t of (data.tools || [])) {
    const tr = document.createElement('tr');
    const overridePill = (t.frequencyOverride_inMinutes === undefined || t.frequencyOverride_inMinutes === null)
      ? '<span class="pill">-</span>'
      : `<span class="pill warn">${escapeHtml(t.frequencyOverride_inMinutes)}</span>`;

    const upStatus = isToolUp(t);
    const statusPill = upStatus === true ? '<span class="pill ok">up</span>'
      : upStatus === false ? '<span class="pill bad">down</span>'
      : '<span class="pill">?</span>';

    tr.innerHTML = `
      <td class="mono">${escapeHtml(t.name || '')}</td>
      <td>${statusPill}</td>
      <td>${t.stateCheckFrequency_inMinutes ?? ''}</td>
      <td>${overridePill}</td>
      <td class="mono">${formatTimestamp(t.lastTimeToolWasUp)}</td>
      <td class="actions-cell">
        <button data-act="delete" class="danger">Unwatch</button>
        <button data-act="freq" class="primary">Set Freq</button>
      </td>
    `;

    for (const btn of tr.querySelectorAll('button')) {
      btn.addEventListener('click', async () => {
        const act = btn.dataset.act;
        if (act === 'delete') {
          await apiFetch('/v1/admin/tools', { method: 'DELETE', body: JSON.stringify({ name: t.name }) });
        }
        if (act === 'freq') {
          await promptFrequencyChange('tool', t.name);
        }
        await refreshAll();
      });
    }

    body.appendChild(tr);
  }
}

/**
 * Refresh websites table.
 */
async function refreshWebsites() {
  const data = await apiFetch('/v1/admin/websites');
  const body = $('websitesBody');
  body.innerHTML = '';
  for (const w of (data.websites || [])) {
    const tr = document.createElement('tr');
    const state = (w.state || '').toLowerCase();
    const pill = state === 'up'
      ? '<span class="pill ok">up</span>'
      : (state === 'down'
        ? '<span class="pill bad">down</span>'
        : '<span class="pill">?</span>');

    tr.innerHTML = `
      <td class="mono">${escapeHtml(w.url || '')}</td>
      <td>${pill}</td>
      <td class="mono">${w.isDownMessageHasBeenSent ?? ''}</td>
      <td><button class="danger">Remove</button></td>
    `;

    tr.querySelector('button').addEventListener('click', async () => {
      await apiFetch('/v1/admin/websites', { method: 'DELETE', body: JSON.stringify({ url: w.url }) });
      await refreshAll();
    });

    body.appendChild(tr);
  }
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

  // Already has a valid protocol
  if (/^https?:\/\//i.test(input)) {
    return [input];
  }

  // Remove any leading protocol-like patterns that are incomplete
  input = input.replace(/^[a-z]+:\/*/i, '');

  // Validate domain pattern (basic check)
  const domainPattern = /^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+(\/.*)?$/i;
  if (!domainPattern.test(input)) {
    return [];
  }

  // Add both http and https variants
  return [`http://${input}`, `https://${input}`];
}

/**
 * Add website from input.
 */
async function addWebsite() {
  const rawUrl = ($('websiteUrl').value || '').trim();
  if (!rawUrl) return;

  const urls = normalizeWebsiteUrl(rawUrl);
  if (urls.length === 0) {
    alert('Invalid URL. Please enter a valid domain (e.g., example.com or https://example.com/health)');
    return;
  }

  for (const url of urls) {
    await apiFetch('/v1/admin/websites', { method: 'POST', body: JSON.stringify({ url }) });
  }
  $('websiteUrl').value = '';
  await refreshAll();
}

/**
 * Refresh backups table.
 */
async function refreshBackups() {
  const data = await apiFetch('/v1/admin/backups');
  const body = $('backupsBody');
  body.innerHTML = '';
  for (const b of (data.backups || [])) {
    const tr = document.createElement('tr');
    const overridePill = (b.frequencyOverride_inMinutes === undefined || b.frequencyOverride_inMinutes === null)
      ? '<span class="pill">-</span>'
      : `<span class="pill warn">${escapeHtml(b.frequencyOverride_inMinutes)}</span>`;

    tr.innerHTML = `
      <td class="mono">${escapeHtml(b.name || '')}</td>
      <td>${b.stateCheckFrequency_inMinutes ?? ''}</td>
      <td>${overridePill}</td>
      <td class="mono">${formatTimestamp(b.mostRecentBackupFile_creationDate)}</td>
      <td class="actions-cell">
        <button data-act="delete" class="danger">Unwatch</button>
        <button data-act="freq" class="primary">Set Freq</button>
      </td>
    `;

    for (const btn of tr.querySelectorAll('button')) {
      btn.addEventListener('click', async () => {
        const act = btn.dataset.act;
        if (act === 'delete') {
          await apiFetch('/v1/admin/backups', { method: 'DELETE', body: JSON.stringify({ name: b.name }) });
        }
        if (act === 'freq') {
          await promptFrequencyChange('backup', b.name);
        }
        await refreshAll();
      });
    }

    body.appendChild(tr);
  }
}

/**
 * Refresh Google Drive config section.
 */
async function refreshGdrive() {
  const data = await apiFetch('/v1/admin/google-drive/folders');
  $('gdriveList').value = JSON.stringify(data.foldersToCheck || [], null, 2);
}

/**
 * Upsert a Google Drive folder config object.
 */
async function upsertGdrive() {
  const raw = ($('gdriveFolderJson').value || '').trim();
  if (!raw) return;
  const obj = JSON.parse(raw);
  await apiFetch('/v1/admin/google-drive/folders', { method: 'POST', body: JSON.stringify(obj) });
  await refreshGdrive();
}

/**
 * Remove a Google Drive folder config by name.
 */
async function removeGdrive() {
  const name = ($('gdriveRemoveName').value || '').trim();
  if (!name) return;
  await apiFetch('/v1/admin/google-drive/folders', { method: 'DELETE', body: JSON.stringify({ name }) });
  await refreshGdrive();
}

/**
 * Refresh raw config view.
 */
async function refreshConfig() {
  const data = await apiFetch('/v1/admin/config');
  $('configView').value = JSON.stringify(data, null, 2);
}

/**
 * Escape HTML entities.
 *
 * @param {any} s - Input.
 * @returns {string} Escaped string.
 */
function escapeHtml(s) {
  return String(s)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

/**
 * Wire up UI events.
 */
function wireUi() {
  $('btnSave').addEventListener('click', async () => {
    await saveSettings();
  });

  $('btnReload').addEventListener('click', async () => {
    try {
      setStatus('Loading...');
      await refreshAll();
      setStatus('Loaded.');
    } catch (e) {
      setStatus(String(e));
    }
  });

  for (const btn of document.querySelectorAll('#tabs .tab')) {
    btn.addEventListener('click', async () => {
      setActiveTab(btn.dataset.tab);
    });
  }

  $('toolsRefresh').addEventListener('click', () => refreshAll().catch((e) => setStatus(String(e))));
  $('websitesRefresh').addEventListener('click', () => refreshAll().catch((e) => setStatus(String(e))));
  $('websiteAdd').addEventListener('click', () => addWebsite().catch((e) => setStatus(String(e))));
  $('backupsRefresh').addEventListener('click', () => refreshAll().catch((e) => setStatus(String(e))));
  $('gdriveRefresh').addEventListener('click', () => refreshAll().catch((e) => setStatus(String(e))));
  $('gdriveUpsert').addEventListener('click', () => upsertGdrive().catch((e) => setStatus(String(e))));
  $('gdriveRemove').addEventListener('click', () => removeGdrive().catch((e) => setStatus(String(e))));
  $('refreshIcon').addEventListener('click', () => triggerRefreshWithAnimation());
}

/**
 * Fetch and display API version in footer.
 */
async function fetchApiVersion() {
  try {
    const res = await fetch('/version');
    if (res.ok) {
      const data = await res.json();
      $('apiVersion').textContent = data.version || 'unknown';
    } else {
      $('apiVersion').textContent = 'unavailable';
    }
  } catch (e) {
    $('apiVersion').textContent = 'unavailable';
  }
}

/**
 * Fetch and display Web image version in footer.
 */
async function fetchWebVersion() {
  try {
    const res = await fetch('/web-version.json');
    if (res.ok) {
      const data = await res.json();
      $('webVersion').textContent = data.version || 'unknown';
    } else {
      $('webVersion').textContent = 'local';
    }
  } catch (e) {
    $('webVersion').textContent = 'local';
  }
}

/**
 * Start auto-refresh interval.
 */
function startAutoRefresh() {
  if (autoRefreshInterval) {
    clearInterval(autoRefreshInterval);
  }
  autoRefreshInterval = setInterval(async () => {
    try {
      await refreshAll();
    } catch (e) {
      // Silently fail on auto-refresh errors
    }
  }, AUTO_REFRESH_INTERVAL_MS);
}

/**
 * Start time ago update interval (every 10 seconds).
 */
function startTimeAgoUpdater() {
  if (timeAgoInterval) {
    clearInterval(timeAgoInterval);
  }
  timeAgoInterval = setInterval(() => {
    updateTimeAgoDisplay();
  }, 10000); // Update every 10 seconds
}

/**
 * Trigger refresh with animation.
 */
async function triggerRefreshWithAnimation() {
  const btn = $('refreshIcon');
  if (btn) {
    btn.classList.add('spinning');
  }
  try {
    setStatus('Refreshing...');
    await refreshAll();
    setStatus('Refreshed.');
  } catch (e) {
    setStatus(String(e));
  } finally {
    if (btn) {
      btn.classList.remove('spinning');
    }
  }
}

/**
 * Initialize admin UI.
 */
async function init() {
  loadSettings();
  wireUi();
  fetchApiVersion();
  fetchWebVersion();
  startAutoRefresh();
  startTimeAgoUpdater();
  try {
    setStatus('Loading...');
    await refreshAll();
    setStatus('Loaded.');
  } catch (e) {
    setStatus(String(e));
  }
}

init();
