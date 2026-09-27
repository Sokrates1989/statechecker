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
    button.disabled = true;
    try {
        const result = await apiCall('/v1/admin/notifications/test', 'POST', {
            level,
            message: t('notifications.testMessage', {
                level: t(level === 'info' ? 'notifications.levelInfo' : 'notifications.levelError')
            })
        });
        showStatus(
            result.failed > 0
                ? t('notifications.partial', { delivered: result.delivered, failed: result.failed })
                : t('notifications.sent', { count: result.delivered }),
            result.failed > 0 ? 'warning' : 'success'
        );
    } catch (error) {
        const codes = [
            'telegram_disabled', 'telegram_recipients_missing',
            'telegram_token_invalid', 'telegram_delivery_failed'
        ];
        const code = codes.find((item) => error.message.includes(item));
        showStatus(t(code ? `notifications.${code}` : 'notifications.sendFailed'), 'error');
    } finally {
        button.disabled = false;
    }
}
