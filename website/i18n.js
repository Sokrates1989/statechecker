/**
 * Look up admin UI messages from the bundled English and German catalogs.
 * The browser language selects a catalog; unsupported languages use English.
 */
(() => {
    const catalogs = window.STATECHECKER_MESSAGES || {};
    const browserLanguage = (navigator.language || 'en').split('-')[0].toLowerCase();
    const locale = Object.hasOwn(catalogs, browserLanguage) ? browserLanguage : 'en';

    window.statecheckerLocale = locale;

    /**
     * Translate a semantic message key and replace its named placeholders.
     *
     * @param {string} key - Message identifier.
     * @param {Record<string, string>} [values] - Values for named placeholders.
     * @returns {string} Localized message.
     */
    window.statecheckerT = function statecheckerT(key, values = {}) {
        const message = catalogs[locale]?.[key] ?? catalogs.en?.[key];
        if (typeof message !== 'string') {
            throw new Error(`Missing translation: ${key}`);
        }

        return message.replace(/\{([a-zA-Z0-9_]+)\}/g, (_, name) => {
            if (!Object.hasOwn(values, name)) {
                throw new Error(`Missing translation value: ${key}.${name}`);
            }
            return String(values[name]);
        });
    };
})();
