/** English messages for the Statechecker admin UI. */
window.STATECHECKER_MESSAGES = window.STATECHECKER_MESSAGES || {};
window.STATECHECKER_MESSAGES.en = {
    'websites.addBeforeRemovingExamples': 'These are example websites. Add a website you want to monitor before removing them.',
    'websites.confirmRemove': 'Remove website "{url}" from monitoring?',
    'websites.removed': 'Website "{url}" removed',
    'websites.removeFailed': 'Website "{url}" is still being watched. Please try again.',
    'websites.removeRequestFailed': 'Failed to remove website: {error}',
    'notifications.tab': 'Notifications',
    'notifications.title': 'Telegram notifications',
    'notifications.hint': 'Send a test message to the configured chat IDs. Bot credentials stay on the server.',
    'notifications.errorChats': 'Error chat IDs',
    'notifications.infoChats': 'Info chat IDs',
    'notifications.none': 'None configured',
    'notifications.disabled': 'Telegram is disabled on this server.',
    'notifications.level': 'Message level',
    'notifications.levelError': 'Error',
    'notifications.levelInfo': 'Info',
    'notifications.send': 'Send test notification',
    'notifications.testMessage': 'Statechecker Telegram test notification ({level}).',
    'notifications.sent': 'Test notification delivered to {count} chat(s).',
    'notifications.partial': 'Delivered to {delivered} chat(s); failed for {failed}.',
    'notifications.loadFailed': 'Could not load Telegram settings.',
    'notifications.telegram_disabled': 'Telegram is disabled on this server.',
    'notifications.telegram_recipients_missing': 'No chat IDs are configured for this level.',
    'notifications.telegram_token_invalid': 'The server bot token is missing or invalid.',
    'notifications.telegram_delivery_failed': 'Telegram did not accept the test notification.',
    'notifications.sendFailed': 'Test notification could not be sent.'
};
