/** Telegram test notification controls for the authenticated admin UI. */

function initNotificationsTab() {
    const t = window.statecheckerT;
    const labels = {
        'notifications-title': 'notifications.title',
        'notifications-hint': 'notifications.hint',
        'notifications-disabled': 'notifications.disabled',
        'notifications-error-label': 'notifications.errorChats',
        'notifications-info-label': 'notifications.infoChats',
        'notifications-level-label': 'notifications.level',
        'notifications-send': 'notifications.send'
    };
    for (const [id, key] of Object.entries(labels)) {
        document.getElementById(id).textContent = t(key);
    }

    const levelSelect = document.getElementById('notifications-level');
    for (const level of ['error', 'info']) {
        const option = document.createElement('option');
        option.value = level;
        option.textContent = t(level === 'info' ? 'notifications.levelInfo' : 'notifications.levelError');
        levelSelect.appendChild(option);
    }
    document.getElementById('notifications-send').addEventListener('click', sendNotificationTest);
}

async function loadNotifications() {
    const t = window.statecheckerT;
    try {
        const settings = await apiCall('/v1/admin/notifications');
        const formatChats = (chats) => chats.length > 0 ? chats.join(', ') : t('notifications.none');
        document.getElementById('notifications-error-chats').textContent = formatChats(settings.error_chat_ids);
        document.getElementById('notifications-info-chats').textContent = formatChats(settings.info_chat_ids);
        document.getElementById('notifications-disabled').classList.toggle('hidden', settings.telegram_enabled);
        document.getElementById('notifications-send').disabled = !settings.telegram_enabled;
    } catch (error) {
        showStatus(t('notifications.loadFailed'), 'error');
    }
}

async function sendNotificationTest() {
    const t = window.statecheckerT;
    const button = document.getElementById('notifications-send');
    const level = document.getElementById('notifications-level').value;
    document.getElementById('notifications-test-result').classList.add('hidden');
    button.disabled = true;
    try {
        const result = await apiCall('/v1/admin/notifications/test', 'POST', {
            level,
            message: t('notifications.testMessage', {
                level: t(level === 'info' ? 'notifications.levelInfo' : 'notifications.levelError')
            })
        });
        const summary = result.failed > 0
            ? t('notifications.partial', { delivered: result.delivered, failed: result.failed })
            : t('notifications.sent', { count: result.delivered });
        renderNotificationTestResult(summary, result);
        showStatus(summary, result.failed > 0 ? 'warning' : 'success');
    } catch (error) {
        const details = error.apiDetails;
        const codes = [
            'telegram_disabled', 'telegram_recipients_missing',
            'telegram_token_missing', 'telegram_token_quoted',
            'telegram_token_invalid', 'telegram_delivery_failed'
        ];
        const code = codes.find((item) => details?.code === item || details === item || error.message.includes(item));
        const summary = code ? t(`notifications.${code}`)
            : [401, 403].includes(error.httpStatus) ? t('notifications.permissionDenied')
            : error instanceof TypeError ? t('notifications.apiUnreachable')
            : Number.isInteger(error.httpStatus)
                ? t('notifications.apiFailed', { status: error.httpStatus })
                : t('notifications.sendFailed');
        renderNotificationTestResult(summary, details);
        showStatus(summary, 'error');
    } finally {
        button.disabled = false;
    }
}

/** Show a persistent, translated per-chat outcome without displaying provider text. */
function renderNotificationTestResult(summary, details) {
    const t = window.statecheckerT;
    const panel = document.getElementById('notifications-test-result');
    const list = document.getElementById('notifications-test-recipients');
    const diagnostic = document.getElementById('notifications-test-diagnostic-id');
    document.getElementById('notifications-test-summary').textContent = summary;
    list.replaceChildren();
    const reasons = [
        'chat_not_found', 'bot_blocked', 'chat_forbidden', 'token_rejected',
        'rate_limited', 'provider_unavailable', 'provider_rejected',
        'network_timeout', 'network_error', 'unexpected_error'
    ];
    for (const result of Array.isArray(details?.results) ? details.results : []) {
        const item = document.createElement('li');
        const reason = result.status === 'sent' ? 'delivered'
            : reasons.includes(result.reason) ? result.reason : 'unexpected_error';
        item.textContent = t('notifications.recipientResult', {
            chat: String(result.chat_id),
            result: t(`notifications.reason.${reason}`),
            status: Number.isInteger(result.provider_status)
                ? result.provider_status : t('notifications.notAvailable')
        });
        list.appendChild(item);
    }
    const hasDiagnosticId = typeof details?.diagnostic_id === 'string';
    diagnostic.classList.toggle('hidden', !hasDiagnosticId);
    diagnostic.textContent = hasDiagnosticId
        ? t('notifications.diagnosticId', { id: details.diagnostic_id }) : '';
    panel.classList.remove('hidden');
}
